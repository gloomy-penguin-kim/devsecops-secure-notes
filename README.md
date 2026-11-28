#### The SecureNotes CI/CD pipeline is implemented using GitHub Actions and is triggered by pushes to the main branch and pull requests targeting main.


```bash
docker run --rm -d `
    --name secure-notes-lab10 `
    --read-only `
    --cap-drop=ALL `
    --tmpfs /tmp `
    --env-file .env `
    -p 127.0.0.1:5001:5000 `
    secure-notes:main
```

```text
Action	                            Commit SHA
actions/checkout	                11bd71901bbe5b1630ceea73d27597364c9af683
sigstore/cosign-installer	        6f9f17788090df1f26f669e9d70d6ae9567deba6
actions/attest-build-provenance	    4d101475d8b20a2381f78447822ac1eab6504dd8
```

#### There are two parts to CI.yml: 
- **build-test:** checksout the repository, sets up python, installs dependencies, checks python syntax with compileall and then runs the application tests 
- **deploy:** after a successful build-test, it authenticates with AWS via OIDC credentials and uses the github-actions-deploy2 IAM role. 
	- permissions re restricted to contents: read and requring an id-token to write 

#### SAST.yml
- Examines code and configuration for insecure programming practices.
- This introduces Semgrep to perform Static Application Security Testing (SAST) automatically in Github Actions.  
- Without actually running the application, SAST examines source code and configurationf iles to look for security weaknesses 
- It is pointed at .smegrep/custom-rules.yml 

#### SCA.yml 
- Examines third-party dependencies for known vulnerabilities.
- Trivy is used to scan application dependencies for known vulnerabilities and generate a CycloneDX Software Bill of Materials (SBOM).  This is uploaded as a Github Actions artifact.  
- This security gate fails when vulnerabilities are found.  
- Trivy was tested when the Python package PyYAML 5.3.1 was introduced to `requirements.txt` because it was effected by CVE-2020-14343 and would therefore be detected and cause the workflow to fail.  

#### Dependabot.yml 
- Configured to check weelky for dependency updates. 


#### Lab 6 Container Security
I selected python:3.13-slim instead of a distroless image to maintain compatibility with Python dependencies, PostgreSQL connectivity, TLS certificate verification, and shell-based troubleshooting.

The runtime image was hardened by:
- Implementing a multi-stage build.
- Running the application as a non-root user.
- Removing pip and its vulnerable vendored dependencies.
- Patching the vulnerable libzstd1 operating system package.
- Enforcing a read-only root filesystem.
- Dropping all Linux capabilities.
- Providing a temporary writable filesystem for Gunicorn.

The hardened image reduced disk usage from 277 MB to 264 MB and vulnerability findings from 231 to 224.

#### Container.yml 
- Lab 6: 
    - This may read the contents of the app (Secure Notes) source coude, public the image and signature to GHCR (write packages), and obtain a GitHub OIDC token for keyless signing 
    - "Cosign cryptographically signs that immutable reference" - I signed by digest rather than signinig by tag - which is more secure.
    - Hadolint (Haskell Dockerfile Linter) is an open-source linter that checks Dockerfiles for errors and best practices by parsing them into an abstract syntax tree (AST) and using ShellCheck to lint shell commands inside RUN instructions
    - Trivy is the most popular open source security scanner for Vulnerability &, IaC, SBOM discovery, cloud scanning and Kubernetes security.
- Lab 10: 
    - Added attestations: write permission to the build job.
    - Exported the image repository and digest as job outputs.
    - Generated SLSA build provenance.
    - Moved Cosign verification into a separate verify job.
    - Added a deploy job that depends on successful verification.

#### Kubernetes Lab 
The initial kube-bench scan identified 12 automated failures. These items were corrected: 
- Disabled profiling on the API server, controller manager, and scheduler.
- Least privilege: Restricted kubelet service and configuration file permissions to 600.
- Auditing and accountability: Enabled metadata-level API audit logging with log rotation, retention, and backup limits.

The subsequent kube-bench scan reported only three remaining failures, representing a 75% reduction in automated failures. The remaining findings concern etcd ownership, kubelet certificate authority configuration, and service account token expiration.

- Deployment: 
```bash
kubectl get nodes
kubectl get deployments -n lab8
kubectl get pods -n lab8
kubectl logs -n lab8 deployment/secure-notes --tail=5
```
- Pod Security Standard enforced 
```bash 
kubectl get namespace lab8 --show-labels
kubectl get events -n lab8
kubectl get pods -n lab8
kubectl exec -n lab8 deployment/secure-notes -- id
```
- Adding the pod-level and container-level securityContext configurations - k8s/Deployment.yaml 
```bash
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  runAsGroup: 1001
  seccompProfile:
    type: RuntimeDefault
securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
```
- Admission Policy 
    - Installation of Kyverno.
    - Migration from the deprecated ClusterPolicy to ValidatingPolicy.
    - Using CEL to require CPU and memory limits.
    - Testing both compliant and noncompliant configurations.

- Memory segment added/removed for testing of policy. 
 ```bash
        resources:
        limits:
            cpu: "500m"
            memory: "256Mi"
```
- Kube-Bench findings addressed
    - Disabled control plane profiling, 1.2.15, 1.3.2, 1.4.1
    - Restricted kubelet file permissions, 4.1.1, 4.1.9
    - Enabled audit logging and rotation, 1.2.16–1.2.19
    - Disabled extended token expiration, 1.2.30
    - Configured kubelet TLS verification, 1.2.5
Before Totals: 
```text
== Summary total ==
63 checks PASS
12 checks FAIL
56 checks WARN
0 checks INFO
```
After Totals: 
```text
== Summary total ==
75 checks PASS
1 checks FAIL
55 checks WARN
0 checks INFO
```

#### Lab 10 - Supply Chain Provenance and Build Integrity  
- The goal is to build, test, scan, sign, attest, and verify the exact same Docker image before allowing deployment.


`python -c "import secrets; print(secrets.token_hex(32))"`

`flask --app app init-db`
`flask --app app run`


- build the ap 
`docker build -t secure-notes .`

- test out the database connection
`docker run --rm --env-file .env secure-notes flask --app app init-db`

- run the app 
`docker run --rm -p 127.0.0.1:5000:5000 --env-file .env secure-notes`

- run semgrep witin docker locally 
`docker run --rm -v "${PWD}:/src" -w /src semgrep/semgrep semgrep --config auto --config .semgrep/custom-rules.yml --error .`

- run trivy within docker locally 
`docker run --rm -v "${PWD}:/src" aquasec/trivy:0.76.2 fs --scanners vuln --severity CRITICAL --exit-code 1 /src` 

- test an api point 
`Invoke-RestMethod http://localhost:5000/health`

- make a test user 
```powershell 
Invoke-RestMethod `
    -Uri http://localhost:5000/register `
    -Method Post `
    -ContentType "application/json" `
    -Body (@{
        username = "alice"
        password = "local-test-password"
    } | ConvertTo-Json)
```

- test login of the user
```powershell 
$result = Invoke-RestMethod `
    -Uri http://localhost:5000/login `
    -Method Post `
    -ContentType "application/json" `
    -Body (@{
        username = "alice"
        password = "local-test-password"
    } | ConvertTo-Json)

$token = $result.access_token

$headers = @{
    Authorization = "Bearer $token"
}
```

- verify the tables are correct
```sql
SELECT table_name,
       column_name,
       data_type,
       is_nullable,
       column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('users', 'notes')
ORDER BY table_name, ordinal_position;
```

- view the users 
```sql
SELECT u.id AS user_id,
       u.username,
       n.id AS note_id,
       n.content,
       n.created_at
FROM users u
LEFT JOIN notes n
    ON u.id = n.user_id
ORDER BY u.id, n.created_at;
```

- verify your indexes 
```sql 
SELECT tablename,
       indexname,
       indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('users', 'notes');
```

- to reset the data during testing
```sql
TRUNCATE TABLE notes, users RESTART IDENTITY;
```

