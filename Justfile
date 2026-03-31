# datafrey task runner

# Run a service (e.g. `just run mcp`)
run service:
    #!/usr/bin/env bash
    case "{{service}}" in
        mcp)
            docker build -t datafrey-mcp -f packages/datafrey-mcp/Dockerfile .
            docker run --rm -p 8080:8080 datafrey-mcp
            ;;
        *)
            echo "Unknown service: {{service}}"
            exit 1
            ;;
    esac
