-- Create WSO2 Identity Server databases
CREATE DATABASE wso2is_identity;
CREATE DATABASE wso2is_shared;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE wso2is_identity TO postgres;
GRANT ALL PRIVILEGES ON DATABASE wso2is_shared TO postgres;