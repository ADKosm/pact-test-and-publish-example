from invoke import task
from src.provider import app


@task(name='test-consumer')
def test_consumer(ctx):
    print('[INFO] Runs the consumer pact tests')
    ctx.run('pytest src')


@task(name='test-provider')
def test_provider(ctx):
    print('[INFO] Validate pact files against server')
    import threading

    def run_provider():
        app.run('0.0.0.0', port=1234)

    provider = threading.Thread(target=run_provider, daemon=True)
    provider.start()
    ctx.run(
        'pact-verifier '
        '--provider-base-url=http://localhost:1234 '
        '--pact-urls=consumer-service-provider-service.json '
    )


@task(name='run-broker')
def run_broker(ctx):
    print('[INFO] Run pack-broker')
    import time
    ctx.run('docker pull dius/pact-broker:2.27.6-2')
    ctx.run('docker pull postgres:10.5')
    ctx.run('docker-compose up -d')
    time.sleep(5) # prepare


@task(name='publish')
def publish(ctx):
    print('[INFO] Publish test results to pack-broker')
    ctx.run(
        'curl -v -XPUT \-H "Content-Type: application/json" '
        '-d@consumer-service-provider-service.json '
        'http://localhost:8000/pacts/provider/provider-service/consumer/consumer-service/version/1.0.0'
    )

@task(name='kill-broker')
def kill_broker(ctx):
    print('[INFO] Kill broker')
    ctx.run('docker-compose down')

@task(
    name='run-scenario',
    pre=[
        test_consumer,
        test_provider,
        run_broker,
        publish
    ],
    post=[
        kill_broker
    ]
)
def run_scenario(ctx):
    import webbrowser
    webbrowser.open_new_tab('http://localhost:8000')
    print('')
    input('Press Enter to finish scenario')
