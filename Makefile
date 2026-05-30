.PHONY: up pull-model down clean

up:
	docker-compose up -d

pull-model:
	@echo "Pulling nomic-embed-text into ollama container..."
	docker exec -it rag-powered-document-assistant-ollama-1 ollama pull nomic-embed-text

test:
	curl http://localhost:8000/health

logs:
	docker-compose logs -f

down:
	docker-compose down

clean:
	docker-compose down -v
