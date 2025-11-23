/**
 * Bridge script to forward scores from Node.js app to RabbitMQ
 *
 * This script can be used to integrate the existing Node.js dartboard
 * application with the Python RabbitMQ-based application.
 *
 * Usage:
 * 1. Install amqplib: npm install amqplib
 * 2. Run this script alongside your dartboard.js
 * 3. It will listen on port 3001 and forward to RabbitMQ
 */

const express = require('express');
const bodyParser = require('body-parser');
const amqp = require('amqplib');

const app = express();
app.use(bodyParser.json());

// Configuration
const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://guest:guest@localhost:5672';
const RABBITMQ_EXCHANGE = process.env.RABBITMQ_EXCHANGE || 'darts_exchange';
const BRIDGE_PORT = process.env.BRIDGE_PORT || 3001;

let channel = null;
let connection = null;

// Connect to RabbitMQ
async function connectRabbitMQ() {
    try {
        connection = await amqp.connect(RABBITMQ_URL);
        channel = await connection.createChannel();

        // Declare exchange
        await channel.assertExchange(RABBITMQ_EXCHANGE, 'topic', {
            durable: true
        });

        console.log('✓ Connected to RabbitMQ');
        console.log(`  Exchange: ${RABBITMQ_EXCHANGE}`);

        // Handle connection errors
        connection.on('error', (err) => {
            console.error('RabbitMQ connection error:', err);
            setTimeout(connectRabbitMQ, 5000);
        });

        connection.on('close', () => {
            console.log('RabbitMQ connection closed, reconnecting...');
            setTimeout(connectRabbitMQ, 5000);
        });

    } catch (error) {
        console.error('Failed to connect to RabbitMQ:', error.message);
        console.log('Retrying in 5 seconds...');
        setTimeout(connectRabbitMQ, 5000);
    }
}

// Publish score to RabbitMQ
async function publishScore(scoreData) {
    if (!channel) {
        console.error('RabbitMQ channel not available');
        return false;
    }

    try {
        const message = JSON.stringify(scoreData);
        const routingKey = `darts.scores.${scoreData.user || 'unknown'}`;

        channel.publish(
            RABBITMQ_EXCHANGE,
            routingKey,
            Buffer.from(message),
            {
                persistent: true,
                contentType: 'application/json'
            }
        );

        console.log(`→ Published: ${message}`);
        return true;

    } catch (error) {
        console.error('Failed to publish message:', error);
        return false;
    }
}

// HTTP endpoint to receive scores (compatible with existing dartboard.js format)
app.post('/data', async (req, res) => {
    const data = req.body;
    console.log('Received score:', data);

    // Transform the data to match Python app format
    const scoreData = {
        score: parseInt(data.point) || 0,
        multiplier: data.message || 'SINGLE',
        user: data.user || 'Player 1',
        timestamp: new Date().toISOString()
    };

    // Publish to RabbitMQ
    const published = await publishScore(scoreData);

    // Send response
    res.json({
        message: 'Score received and forwarded to RabbitMQ',
        published: published
    });
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        rabbitmq: channel ? 'connected' : 'disconnected',
        timestamp: new Date().toISOString()
    });
});

// Start server
async function start() {
    console.log('🎯 Darts Score Bridge - Node.js to RabbitMQ');
    console.log('=' .repeat(50));

    // Connect to RabbitMQ
    await connectRabbitMQ();

    // Start HTTP server
    app.listen(BRIDGE_PORT, () => {
        console.log(`✓ Bridge server listening on port ${BRIDGE_PORT}`);
        console.log('=' .repeat(50));
        console.log('Ready to forward scores to RabbitMQ!');
        console.log(`POST scores to: http://localhost:${BRIDGE_PORT}/data`);
    });
}

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\nShutting down...');
    if (channel) await channel.close();
    if (connection) await connection.close();
    process.exit(0);
});

// Start the bridge
start().catch(console.error);
