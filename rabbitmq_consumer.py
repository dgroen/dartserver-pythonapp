"""
RabbitMQ Consumer for receiving dart scores
"""
import json
import pika
import time


class RabbitMQConsumer:
    """RabbitMQ consumer for dart scores"""
    
    def __init__(self, config, callback):
        """
        Initialize RabbitMQ consumer
        
        Args:
            config: Dictionary with RabbitMQ configuration
            callback: Function to call when a message is received
        """
        self.config = config
        self.callback = callback
        self.connection = None
        self.channel = None
        self.should_stop = False
        
    def connect(self):
        """Establish connection to RabbitMQ"""
        credentials = pika.PlainCredentials(
            self.config['user'],
            self.config['password']
        )
        
        parameters = pika.ConnectionParameters(
            host=self.config['host'],
            port=self.config['port'],
            virtual_host=self.config['vhost'],
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        
        # Declare exchange
        self.channel.exchange_declare(
            exchange=self.config['exchange'],
            exchange_type='topic',
            durable=True
        )
        
        # Declare queue (auto-generated name)
        result = self.channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        
        # Bind queue to exchange with topic
        self.channel.queue_bind(
            exchange=self.config['exchange'],
            queue=queue_name,
            routing_key=self.config['topic']
        )
        
        print(f"Connected to RabbitMQ: {self.config['host']}:{self.config['port']}")
        print(f"Listening on exchange '{self.config['exchange']}' with topic '{self.config['topic']}'")
        
        return queue_name
    
    def on_message(self, channel, method, properties, body):
        """
        Callback when a message is received
        
        Args:
            channel: Channel object
            method: Method frame
            properties: Properties
            body: Message body
        """
        try:
            # Parse JSON message
            message = json.loads(body.decode('utf-8'))
            print(f"Received message: {message}")
            
            # Process the score
            self.callback(message)
            
            # Acknowledge the message
            channel.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse message: {e}")
            # Reject malformed messages
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            print(f"Error processing message: {e}")
            # Requeue on processing errors
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start(self):
        """Start consuming messages"""
        while not self.should_stop:
            try:
                queue_name = self.connect()
                
                # Start consuming
                self.channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=self.on_message,
                    auto_ack=False
                )
                
                print("Waiting for messages. To exit press CTRL+C")
                self.channel.start_consuming()
                
            except pika.exceptions.AMQPConnectionError as e:
                print(f"Connection error: {e}")
                print("Retrying in 5 seconds...")
                time.sleep(5)
            except KeyboardInterrupt:
                print("Interrupted by user")
                self.stop()
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                print("Retrying in 5 seconds...")
                time.sleep(5)
    
    def stop(self):
        """Stop consuming messages"""
        self.should_stop = True
        if self.channel and self.channel.is_open:
            self.channel.stop_consuming()
        if self.connection and self.connection.is_open:
            self.connection.close()
        print("RabbitMQ consumer stopped")