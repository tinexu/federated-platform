import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///fl_platform.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # AWS Config
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    MODEL_BUCKET = 'fed-learn-models-1w4zzxzc'
    
    # Pricing
    LAMBDA_COST_PER_SECOND = 0.0000166667
    S3_COST_PER_GB = 0.023
