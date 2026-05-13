.PHONY: run api test docker-up docker-down

run:
	uvicorn api.main:app --reload

api:
	uvicorn api.main:app --host 0.0.0.0 --port 8000

test:
	pytest -q

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down
