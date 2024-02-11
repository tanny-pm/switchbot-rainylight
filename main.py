import functions_framework

from rainylight.rainylight import main


# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def pubsub_hundler(cloud_event):
    return main()


if __name__ == "__main__":
    main()
