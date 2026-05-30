.PHONY: up pull-model down clean

up:
	docker-compose up -d

pull-model:
	@echo "Pulling qwen2:1.5b into ollama container..."
	docker exec -it rag-powered-document-assistant-ollama-1 ollama pull qwen2:1.5b

test: curl http://localhost:8000/health

logs: docker-compose logs -f

down:
	docker-compose down

clean:
	docker-compose down -v
