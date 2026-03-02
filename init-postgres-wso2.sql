-- Initialize PostgreSQL databases for WSO2 Identity Server
-- This script is automatically run when PostgreSQL container starts

-- Create WSO2 Identity database
CREATE DATABASE wso2is_identity WITH ENCODING 'UTF8';

-- Create WSO2 Shared database
CREATE DATABASE wso2is_shared WITH ENCODING 'UTF8';

-- Create WSO2 API Manager database
CREATE DATABASE wso2apim_shared WITH ENCODING 'UTF8';
