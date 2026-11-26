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

Write-Host "Login successful"