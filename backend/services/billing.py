class BillingService:
    PRICING = {
        'free': {
            'jobs_per_month': 3,
            'clients_per_job': 3,
            'rounds_per_job': 10,
            'cost_per_round': 0
        },
        'startup': {
            'jobs_per_month': 50,
            'clients_per_job': 10,
            'rounds_per_job': 100,
            'cost_per_round': 0.10
        },
        'enterprise': {
            'jobs_per_month': -1,  # unlimited
            'clients_per_job': -1,
            'rounds_per_job': -1,
            'cost_per_round': 0.05
        }
    }
    
    def estimate_job_cost(self, config):
        # Base cost: Lambda execution
        lambda_cost = config['num_clients'] * config['rounds'] * 0.01
        
        # Storage cost
        storage_cost = 0.023 * config['rounds'] * 0.01  # 10MB per round
        
        # Premium features
        if config.get('gpu_training'):
            lambda_cost *= 10
            
        if config.get('multi_region'):
            lambda_cost *= len(config['deployment_regions'])
            
        return lambda_cost + storage_cost