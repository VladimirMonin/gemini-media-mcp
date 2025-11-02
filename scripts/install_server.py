import typer
from pathlib import Path
import json

app = typer.Typer()

@app.command()
def main(
    gemini_api_key: str = typer.Option(..., "--gemini-api-key", "-k", help="Gemini API Key"),
    config_path: Path = typer.Option("~/.mcp/servers_config.json", "--config-path", "-c", help="Path to MCP servers_config.json"),
):
    """
    Installs the Gemini Media MCP server configuration.
    """
    config_path = config_path.expanduser()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
    else:
        config = {"mcpServers": {}}

    server_config = {
        "command": "python",
        "args": ["-m", "server"],
        "env": {
            "GEMINI_API_KEY": gemini_api_key
        }
    }

    config["mcpServers"]["gemini-media-analyzer"] = server_config

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"✅ Gemini Media MCP server configured in {config_path}")

if __name__ == "__main__":
    app()
