# pull-model.ps1
$container = "rag-powered-document-assistant-ollama-1"
$embed_model = "nomic-embed-text"
$chat_model = "qwen2:1.5b"

Write-Host "🔍 Checking container $container..." -ForegroundColor Cyan
if (docker ps --format "{{.Names}}" | Select-String -Pattern $container) {
    Write-Host "✅ Pulling $embed_model ..." -ForegroundColor Green
    docker exec -it $container ollama pull $embed_model
    Write-Host "✅ Pulling $chat_model ..." -ForegroundColor Green
    docker exec -it $container ollama pull $chat_model
    Write-Host "🎉 Done!" -ForegroundColor Green
} else {
    Write-Host "❌ Container not running. Run 'docker-compose up -d' first." -ForegroundColor Red
}
