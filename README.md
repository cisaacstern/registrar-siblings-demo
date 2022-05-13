# registrar-siblings-demo

From the repo root, build the image:

```console
docker build -t registrar-siblings -f ./Dockerfile ./
```

Run the image, with volume-mounted Docker daemon socket:

```console
docker run -v /var/run/docker.sock:/var/run/docker.sock -it registrar-siblings:latest
```

