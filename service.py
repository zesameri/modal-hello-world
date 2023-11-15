import os, sys
from modal import Image, Stub, Secret
from ddtrace import tracer

tracer.set_tags({"env": "test"})
tracer.configure(enabled=True, partial_flush_enabled=False)
app_name = "modal"
image = (
    Image.debian_slim(python_version="3.11")
    .dockerfile_commands(
        ["COPY --from=datadog/serverless-init /datadog-init /app/datadog-init", 'ENTRYPOINT ["/app/datadog-init"]']
    )
    .pip_install("ddtrace")
)
stub = Stub(name=app_name, image=image)

DD_ENV = Secret.from_dict(
    {
        "DD_SITE": "datadoghq.com",
        "DD_ENV": "test",
        "DD_SERVICE": app_name,
        "DD_LOGS_ENABLED": "true",
        "DD_TRACE_DEBUG": "true",
        "DD_ENV": "test",
        "DD_LOGS_INJECTION": "true",
        "DD_PYTHON_VERSION": "3",
        "S6_BEHAVIOUR_IF_STAGE2_FAILS": "2",
        "S6_LOGGING": "0",
        "S6_READ_ONLY_ROOT": "1",
        "S6_KEEP_ENV": "1",
        "DOCKER_DD_AGENT": "true",
        "DD_APM_INSTRUMENTATION_ENABLED": "host",
    }
)


#
@stub.function(secrets=[Secret.from_name("datadog-secret"), DD_ENV])
@tracer.wrap(name="hello-world", service=app_name)
def f(i):
    import os
    os.environ["DD_TRACE_ENABLED"] = "1"
    # with tracer.trace("foo"):
    if i % 2 == 0:
        print("hello", i)
    else:
        print("world", i, file=sys.stderr)
    return i * i


@stub.local_entrypoint()
def main():
    # Call the function locally.
    print(f.local(1000))

    # Call the function remotely.
    print(f.remote(1000))

    # Parallel map.
    total = 0
    for ret in f.map(range(20)):
        total += ret

    print(total)
    print(os.environ)
