Invoke-RestMethod `
    -Uri http://localhost:5000/register `
    -Method Post `
    -ContentType "application/json" `
    -Body (@{
        username = "alice"
        password = "local-test-password"
    } | ConvertTo-Json)