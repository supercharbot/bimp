"""
Run once: creates Gmail Pub/Sub topic + subscription + watch.
Usage: cd ~/bimp && source venv/bin/activate && python3 -m ingest.setup_pubsub
"""
from google.cloud import pubsub_v1
from google.iam.v1 import policy_pb2
from shared.google_client import get_gmail_service, get_credentials
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = 'bimp-495600'
GMAIL_TOPIC = f'projects/{PROJECT_ID}/topics/bimp-gmail'
GMAIL_SUB = f'projects/{PROJECT_ID}/subscriptions/bimp-gmail-pull'


def setup():
    creds = get_credentials()
    publisher = pubsub_v1.PublisherClient(credentials=creds)
    subscriber = pubsub_v1.SubscriberClient(credentials=creds)

    # Create topic
    try:
        publisher.create_topic(name=GMAIL_TOPIC)
        logger.info(f"Created topic: {GMAIL_TOPIC}")
    except Exception as e:
        if 'ALREADY_EXISTS' in str(e):
            logger.info(f"Topic exists: {GMAIL_TOPIC}")
        else:
            raise

    # Grant Gmail permission to publish
    policy = publisher.get_iam_policy(request={"resource": GMAIL_TOPIC})
    policy.bindings.add(
        role="roles/pubsub.publisher",
        members=["serviceAccount:gmail-api-push@system.gserviceaccount.com"]
    )
    publisher.set_iam_policy(request={"resource": GMAIL_TOPIC, "policy": policy})
    logger.info("Granted Gmail publish permission")

    # Create pull subscription
    try:
        subscriber.create_subscription(name=GMAIL_SUB, topic=GMAIL_TOPIC, ack_deadline_seconds=60)
        logger.info(f"Created subscription: {GMAIL_SUB}")
    except Exception as e:
        if 'ALREADY_EXISTS' in str(e):
            logger.info(f"Subscription exists: {GMAIL_SUB}")
        else:
            raise

    # Set up Gmail watch
    gmail = get_gmail_service()
    watch = gmail.users().watch(
        userId='me',
        body={'topicName': GMAIL_TOPIC, 'labelIds': ['INBOX']}
    ).execute()
    logger.info(f"Gmail watch active, expires: {watch.get('expiration')}")
    logger.info(f"History ID: {watch.get('historyId')}")

    subscriber.close()
    logger.info("Setup complete.")


if __name__ == '__main__':
    setup()
