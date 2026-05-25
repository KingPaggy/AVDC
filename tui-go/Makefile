.PHONY: run build release tidy test clean

run: tidy
	go run main.go

build:
	go build -o avdc-tui

release:
	go build -ldflags="-s -w" -o avdc-tui

tidy:
	go mod tidy

test:
	go test ./... -v

clean:
	rm -f avdc-tui
