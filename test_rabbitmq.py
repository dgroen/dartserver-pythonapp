"""
Test script for sending dart scores to RabbitMQ
"""
import json
import pika
import time
import random
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# RabbitMQ configuration
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
RABBITMQ_VHOST = os.getenv('RABBITMQ_VHOST', '/')
RABBITMQ_EXCHANGE = os.getenv('RABBITMQ_EXCHANGE', 'darts_exchange')

# Test scores
TEST_SCORES = [
    {'score': 20, 'multiplier': 'TRIPLE', 'user': 'Test Player'},
    {'score': 19, 'multiplier': 'DOUBLE', 'user': 'Test Player'},
    {'score': 18, 'multiplier': 'SINGLE', 'user': 'Test Player'},
    {'score': 25, 'multiplier': 'BULL', 'user': 'Test Player'},
    {'score': 25, 'multiplier': 'DBLBULL', 'user': 'Test Player'},
    {'score': 20, 'multiplier': 'SINGLE', 'user': 'Test Player'},
    {'score': 5, 'multiplier': 'TRIPLE', 'user': 'Test Player'},
    {'score': 1, 'multiplier': 'SINGLE', 'user': 'Test Player'},
]


def send_score(channel, score_data, routing_key='darts.scores.test'):
    """Send a score to RabbitMQ"""
    message = json.dumps(score_data)
    
    channel.basic_publish(
        exchange=RABBITMQ_EXCHANGE,
        routing_key=routing_key,
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
            content_type='application/json'
        )
    )
    
    print(f"Sent: {message}")


def main():
    """Main test function"""
    print("RabbitMQ Dart Score Test Publisher")
    print("=" * 50)
    print(f"Host: {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    print(f"Exchange: {RABBITMQ_EXCHANGE}")
    print("=" * 50)
    
    # Connect to RabbitMQ
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        virtual_host=RABBITMQ_VHOST,
        credentials=credentials
    )
    
    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Declare exchange
        channel.exchange_declare(
            exchange=RABBITMQ_EXCHANGE,
            exchange_type='topic',
            durable=True
        )
        
        print("\nConnected to RabbitMQ successfully!")
        print("\nChoose an option:")
        print("1. Send all test scores (one per second)")
        print("2. Send a single random score")
        print("3. Send custom score")
        print("4. Send continuous random scores (Ctrl+C to stop)")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            print("\nSending test scores...")
            for score in TEST_SCORES:
                send_score(channel, score)
                time.sleep(1)
            print("\nAll test scores sent!")
            
        elif choice == '2':
            score = random.choice(TEST_SCORES)
            print("\nSending random score...")
            send_score(channel, score)
            print("\nScore sent!")
            
        elif choice == '3':
            print("\nEnter custom score:")
            score_value = int(input("Score value (0-60): "))
            multiplier = input("Multiplier (SINGLE/DOUBLE/TRIPLE/BULL/DBLBULL): ").upper()
            user = input("User name (optional): ") or "Test Player"
            
            custom_score = {
                'score': score_value,
                'multiplier': multiplier,
                'user': user
            }
            
            print("\nSending custom score...")
            send_score(channel, custom_score)
            print("\nScore sent!")
            
        elif choice == '4':
            print("\nSending continuous random scores...")
            print("Press Ctrl+C to stop")
            
            try:
                while True:
                    # Generate random score
                    score_value = random.choice([15, 16, 17, 18, 19, 20, 25])
                    multiplier = random.choice(['SINGLE', 'DOUBLE', 'TRIPLE'])
                    
                    if score_value == 25:
                        multiplier = random.choice(['BULL', 'DBLBULL'])
                    
                    score = {
                        'score': score_value,
                        'multiplier': multiplier,
                        'user': 'Test Player'
                    }
                    
                    send_score(channel, score)
                    time.sleep(random.uniform(1, 3))
                    
            except KeyboardInterrupt:
                print("\n\nStopped by user")
        
        else:
            print("Invalid choice")
        
        connection.close()
        
    except pika.exceptions.AMQPConnectionError as e:
        print(f"\nError: Could not connect to RabbitMQ")
        print(f"Details: {e}")
        print("\nMake sure RabbitMQ is running and credentials are correct")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == '__main__':
    main()