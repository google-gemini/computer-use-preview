# Puppeteer Computer User Image

A container image for driving a Chrome browser using [Puppeteer](https://pptr.dev/).

## Getting Started

Build the image:

```
docker build . -t puppeteer-computer
```

Run the container:

```
docker run --name=puppeteer-computer --rm --detach puppeteer-computer
```

Open a webpage:

```
docker exec puppeteer-computer run-command '{"name":"navigate", "args":{"url": "https://google.com"}}'
```

Shut down the container:

```
docker stop puppeteer-computer
```

## Available commands

| Function Name                                 | Description                     | Example                                     |
| :-------------------------------------------- | :------------------------------ | :------------------------------------------ |
| `navigate(url: str)`                          | Navigate to a URL               | `{"name":"navigate", "args":{"url": "https://google.com"}}` |
| `click_at(x: int, y: int)`                    | Click at coordinates            | `{"name":"click_at", "args":{"x": 100, "y": 200}}`                  |
| `hover_at(x: int, y: int)`                    | Hover at coordinates            | `{"name":"hover_at", "args":{"x": 50, "y": 300}}`                   |
| `type_text_at(y: int, x: int, text: str, clear_existing_text: bool)` | Type text at coordinates        | `{"name":"type_text_at", "args":{"x": 150, "y": 75, "text": "Hello"}}` |
| `scroll_document(direction: str)`             | Scroll document                 | `{"name":"scroll_document", "args":{"direction": "down"}}`       |
| `go_back()`                                   | Go back                         | `{"name":"go_back"}`                               |
| `go_forward()`                                | Go forward                      | `{"name":"go_forward"}`                            |
| `search()`                                    | Search                          | `{"name":"search"}`                                |
| `wait_5_seconds()`                            | Wait for 5 seconds              | `{"name":"wait_5_seconds"}`                        |
| `key_combination(keys: str[])`                | Enter a key combination         | `{"name":"key_combination", "args":{"keys": ["Control","C"]}}`  |
| `screenshot()`                                | Take a screenshot               | `{"name":"screenshot"}`                            |

## HTTP API

By default, the image runs an HTTP server that listens for computer use commands on `$PORT`.

1. Run the container and bind port `8080`.

    ```
    docker run --name=puppeteer-computer --rm --detach -p 8080:8080 -e PORT=8080 puppeteer-computer
    ```

2. Send a command by `POST`ing a JSON payload in the form of `{"command": "<command>"}` to http://localhost:8080/:

    ```
    curl --request POST \
        --header "Content-Type: application/json" \
        --data '{"name":"navigate", "args":{"url": "https://en.wikipedia.org/wiki/Python"}}' \
        http://localhost:8080/
    ```


3. Clean up:

    ```
    docker stop puppeteer-computer
    ```

## Pub/Sub API

The image is also able to listen for computer use commands sent over a Pub/Sub signaling channel. This allows it to be deployed as a Cloud Run Job that does not allow HTTP ingress.

1. To run a container listening on Pub/Sub set the `USE_PUBSUB=true` environment variable:

    ```
    docker run --name=puppeteer-computer --rm -it \
        -e USE_PUBSUB=true \
        -e PUBSUB_PROJECT_ID=<project-id> \
        -e SESSION_ID=123 \
        puppeteer-computer
    ```
    
    The `PUBSUB_PROJECT_ID` and `SESSION_ID` are used to configure the Pub/Sub topic

2. Send a command by publishing to the `projects/<project-id>/topics/commands-123` topic:
    
    ```
    export TOPIC=projects/<project-id>/topics/commands-123
    gcloud pubsub topics publish $TOPIC --message='navigate(url: https://google.com/)'
    ```

3. Clean up:

    ```
    docker stop puppeteer-computer
    ```
