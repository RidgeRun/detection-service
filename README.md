## RidgeRun Detection Microservice 1.0.0

Detection Microservice detects in the input stream the target objects described in a text prompt.
The microservice uses the NanoOwl generative AI model that allows open vocabulary detection.
Meaning that the user can provide a list of objects that are not bound to any specific classes.

The input stream is obtained from VST. By default, the first stream available will be selected but
the user can select a specific stream through the server using the [/source](api/openapi.yaml) request.

Also, the objects to detect can be defined through the server using the [/search](api/openapi.yaml) request, with
the list of objects and corresponding thresholds.

The application will output the detection object bounding boxes and classes in Metropolis
Minimal Schema through a Redis Stream called detection.

When used with a 360 video image of high resolution, the objects may be to small for the detection model after
image preprocessing. So SAHI was incorporated as an option to split the image and detect these small objects.
By default sahi is disabled and the whole image is used at once, but it can be enabled by setting the vertical and
horizontal slices arguments. If enabled the application will split the image into an overlapping grid of image slices,
and detect objects for each slice, and then the results are merged to provide the bounding boxes. As you can foresee
with SAHI the processing is slower since the detection will be run more than once.

### Running the service

The project is configured (via setup.py) to install the service with the name __detection__. So to install it run:

```bash
pip install .
```

Then you will have the service with the following options:

```bash
usage: detection [-h] [--port PORT] [--host HOST] [--objects OBJECTS] [--thresholds THRESHOLDS]

options:
  -h, --help            show this help message and exit
  --port PORT           Port for server
  --host HOST           Server ip address
  --objects OBJECTS     List of objects to detect, example: 'a person,a box,a ball'
  --thresholds THRESHOLDS
                        List of thresholds corresponding to the objects, example: 0.1,0.2,0.65
  --vertical-slices VERTICAL_SLICES
                        Divide the image in given amount of vertical slices to detect small objects
  --horizontal-slices HORIZONTAL_SLICES
                        Divide the image in given amount of horizontal slices to detect small objects
```

Notice that you can set the default detection using the objects and thresholds arguments,
if not provided "a person" with a threshold of 0.2 will be used.


```bash
detection
```

This will start the service in address 127.0.0.0 and port 5010. If you want to serve in a
different port or address, use the __--port__ and __--host__ options.

## AI Agent Docker


### Build the container

You can build the detection microservice container using the Dockerfile in the docker directory.
This includes a base genai image and the dependencies to run the ai-agent microservice application.

First, we need to prepare the context directory for this build, you need to create a directory
and include this repository and the rrms-utils project. The Dockerfile will look for both packages
in the context directory and copy them to the container.

```bash
detection-context/
├── detection
└── rrms-utils
```

Then build the container image with the following command:

```bash
DOCKER_BUILDKIT=0 docker build --network=host --tag ridgerun/detection-service --file detection-context/detection/docker/Dockerfile detection-context/
```

Change detection-context/ to your context's path and the tag to the name you want to give to your image.

### Launch the container

The container can be launched by running the following command:

```bash
docker run --runtime nvidia -it --network host --name detection-service  ridgerun/detection-service:latest detection --host 0.0.0.0
```

Here we are creating a container called detection that will start the detection application, launching
the server and detection from the first VST stream available.
