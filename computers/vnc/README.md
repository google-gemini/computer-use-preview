# VNC Computer

A container image for driving a headful Chrome browser using [Puppeteer](https://pptr.dev/) and TigerVNC[https://tigervnc.org/].

## Getting Started

Build the image:

```
docker build . -t vnc-computer
```

Run the container:

```
docker run --name=vnc-computer --rm --detach vnc-computer
```

Open a webpage:

```
docker exec vnc-computer run-command '{"name":"navigate", "args":{"url": "https://google.com"}}'
```

Shut down the container:

```
docker stop vnc-computer
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

The image runs an HTTP server that provide VNC access via [noVNC](https://novnc.com/) and a REST API for issuing computer use commands.

1. Run the container and bind port `8080`.

    ```
    docker run --name=vnc-computer --rm --detach -p 8080:8080 -it vnc-computer
    ```

2. Send a command by `POST`ing a JSON payload in the form of `{"command": "<command>"}` to http://localhost:8080/api:

    ```
    curl --request POST \
    --header "Content-Type: application/json" \
    --data '{"name":"navigate", "args":{"url": "https://en.wikipedia.org/wiki/Python"}}' \
    http://localhost:8080/api
    ```

3. Connect via VNC by opening http://localhost:8080/vnc_lite.html in your browser.


4. Clean up:

    ```
    docker stop vnc-computer
    ```

## Deploying to Cloud Run

1. set some defaults:

    ```
    export PROJECT_ID=<YOUR-GCP-PROJECT_ID>
    export REGION=us-east1
    export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
    gcloud config set project ${PROJECT_ID}
    gcloud config set run/region ${REGION}
    ```

2. build the image:

    ```
    docker build . -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/computer-use/vnc-computer:latest
    ```

3. push to artifact registry:

    ```
    docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/computer-use/vnc-computer:latest
    ```

4. deploy to cloud run:

    ```
    gcloud beta run deploy vnc-computer \
    --scaling=1 \
    --cpu 8 \
    --memory 32G \
    --allow-unauthenticated \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/computer-use/vnc-computer:latest
    ```

5. send it a request:

    ```
    curl --request POST \
    --header "Content-Type: application/json" \
    --data '{"name":"navigate", "args":{"url": "https://en.wikipedia.org/wiki/Python"}}' \
    "https://vnc-computer-${PROJECT_NUMBER}.us-east1.run.app/api"
    ```