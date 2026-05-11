-- Initialize PostgreSQL databases for WSO2 Identity Server
-- This script is automatically run when PostgreSQL container starts

-- Create WSO2 Identity database
CREATE DATABASE wso2is_identity WITH ENCODING 'UTF8';

-- Create WSO2 Shared database
CREATE DATABASE wso2is_shared WITH ENCODING 'UTF8';

-- Create WSO2 API Manager database
CREATE DATABASE wso2apim_shared WITH ENCODING 'UTF8';

-- Connect to wso2is_identity to create required tables
\c wso2is_identity

-- Enable uuid extension if not present
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create required WSO2IS user management tables
CREATE TABLE IF NOT EXISTS um_domain (
    UM_DOMAIN_ID SERIAL NOT NULL,
    UM_DOMAIN_NAME VARCHAR(255) NOT NULL UNIQUE,
    UM_CREATED_DATE BIGINT,
    PRIMARY KEY(UM_DOMAIN_ID)
);

CREATE TABLE IF NOT EXISTS um_tenant (
    UM_ID SERIAL NOT NULL,
    UM_DOMAIN_NAME VARCHAR(255) NOT NULL,
    UM_CREATED_DATE BIGINT,
    UM_EMAIL VARCHAR(255),
    UM_ACTIVE BOOLEAN DEFAULT TRUE,
    PRIMARY KEY(UM_ID),
    FOREIGN KEY(UM_DOMAIN_NAME) REFERENCES um_domain(UM_DOMAIN_NAME)
);

-- Connect to wso2is_shared to create required tables
\c wso2is_shared

-- Enable uuid extension if not present
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
