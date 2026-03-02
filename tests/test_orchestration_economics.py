"""
Test suite for cluster orchestrator and cost optimization
"""

import pytest
import json
from src.cluster_orchestrator import (
    MCDCOrchestrator, MCDCLocation, NetworkLink,
    DeploymentRegion, CostOptimizationStrategy,
    FederationProtocol, MobileContainerDC
)
from src.cost_optimization_engine import (
    ComprehensiveEconomicModel, CloudProvider, FPGABoardModel
)


class TestMCDCOrchestrator:
    """Test cluster orchestrator functionality"""
    
    @pytest.fixture
    def orchestrator(self):
        return MCDCOrchestrator(num_mcdc=10)
    
    def test_add_mcdc(self, orchestrator):
        """Test adding MCDC to cluster"""
        loc = MCDCLocation(
            location_id="TEST-1",
            region=DeploymentRegion.NORTH_AMERICA,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA"
        )
        mcdc = orchestrator.add_mcdc("test_mcdc", loc, num_fpgas=500)
        assert "test_mcdc" in orchestrator.mcdc_list
        assert mcdc.num_fpgas == 500
    
    def test_cluster_status(self, orchestrator):
        """Test cluster status report"""
        loc = MCDCLocation(
            location_id="TEST-2",
            region=DeploymentRegion.EUROPE,
            latitude=51.5074,
            longitude=-0.1278,
            city="London",
            country="UK"
        )
        orchestrator.add_mcdc("london_mcdc", loc, num_fpgas=500)
        
        status = orchestrator.get_cluster_status()
        assert status['num_mcdc'] == 1
        assert status['total_fpga'] == 500
        assert status['compression_ratio'] == 500.0
    
    def test_network_links(self, orchestrator):
        """Test network link management"""
        loc1 = MCDCLocation("A", DeploymentRegion.NORTH_AMERICA, 40.7128, -74.0060, "NYC", "USA")
        loc2 = MCDCLocation("B", DeploymentRegion.EUROPE, 51.5074, -0.1278, "LON", "UK")
        
        orchestrator.add_mcdc("mcdc_a", loc1)
        orchestrator.add_mcdc("mcdc_b", loc2)
        
        link = NetworkLink(
            source_mcdc="mcdc_a",
            dest_mcdc="mcdc_b",
            bandwidth_mbps=100000,
            latency_ms=10
        )
        orchestrator.add_network_link(link)
        
        # Check bidirectional link was created
        assert len(orchestrator.network_graph["mcdc_a"]) >= 1
        assert len(orchestrator.network_graph["mcdc_b"]) >= 1
    
    def test_cost_optimization(self, orchestrator):
        """Test placement optimization"""
        loc = MCDCLocation(
            location_id="OPT-1",
            region=DeploymentRegion.NORTH_AMERICA,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA"
        )
        orchestrator.add_mcdc("opt_mcdc", loc)
        
        result = orchestrator.optimize_placement("opt_mcdc", 15.0)
        assert 'recommendations' in result
        assert result['strategy'] == 'balanced'
    
    def test_federation_broadcast(self, orchestrator):
        """Test federation protocol"""
        loc = MCDCLocation("FED", DeploymentRegion.ASIA_PACIFIC, 35.6762, 139.6503, "Tokyo", "Japan")
        orchestrator.add_mcdc("fed_mcdc", loc)
        
        fed = FederationProtocol(orchestrator)
        result = fed.broadcast_dictionary("test_hash_123", "fed_mcdc")
        
        assert 'propagated_to' in result
        assert "fed_mcdc" in result['propagated_to']


class TestCostOptimization:
    """Test cost optimization engine"""
    
    @pytest.fixture
    def model(self):
        return ComprehensiveEconomicModel(
            num_fpga=5000,
            fpga_board_model=FPGABoardModel.XILINX_U50,
            lifespan_years=5
        )
    
    def test_fpga_capex(self, model):
        """Test FPGA capital expenditure calculation"""
        capex = model.calculate_fpga_capex()
        
        assert 'fpga_boards' in capex
        assert 'container_infrastructure' in capex
        assert 'total_capex' in capex
        assert capex['total_capex'] > 0
    
    def test_fpga_opex(self, model):
        """Test FPGA operational expenditure"""
        opex = model.calculate_fpga_opex(years=5)
        
        assert 'total_power_over_life' in opex
        assert 'total_maintenance_over_life' in opex
        assert 'total_opex_over_life' in opex
        assert opex['total_opex_over_life'] > 0
    
    def test_cloud_costs(self, model):
        """Test cloud storage cost calculation"""
        costs = model.calculate_cloud_costs(
            data_size_eb=15.0,
            provider=CloudProvider.GOOGLE_CLOUD,
            access_pattern="hot"
        )
        
        assert 'total_storage_over_life' in costs
        assert 'total_egress_over_life' in costs
        assert 'total_cloud_cost_over_life' in costs
    
    def test_comparative_analysis(self, model):
        """Test comprehensive cost comparison"""
        analysis = model.comparative_analysis(
            data_size_eb=15.0,
            cloud_provider=CloudProvider.GOOGLE_CLOUD
        )
        
        assert 'fpga_infrastructure' in analysis
        assert 'cloud_storage' in analysis
        assert 'economics' in analysis
        assert 'recommendation' in analysis
        
        # Check economics calculations
        econ = analysis['economics']
        assert 'fpga_cheaper_by' in econ
        assert 'savings_percent' in econ
    
    def test_sensitivity_analysis(self, model):
        """Test sensitivity to parameter changes"""
        # Test power sensitivity
        sensitivity = model.sensitivity_analysis(
            data_size_eb=15.0,
            param_name="power_per_fpga_kw",
            param_range=[0.05, 0.08, 0.10]
        )
        
        assert len(sensitivity) == 3
        for result in sensitivity:
            assert 'fpga_total_cost' in result
            assert 'cloud_total_cost' in result
            assert 'savings' in result
    
    def test_board_model_pricing(self):
        """Test different FPGA board model costs"""
        models = [FPGABoardModel.XILINX_U50, FPGABoardModel.XILINX_U55C, FPGABoardModel.XILINX_U280]
        
        previous_cost = 0
        for model_type in models:
            m = ComprehensiveEconomicModel(fpga_board_model=model_type)
            capex = m.calculate_fpga_capex()
            # Verify costs increase with higher-end boards
            assert capex['total_capex'] >= previous_cost
            previous_cost = capex['total_capex']


class TestMobileContainerDC:
    """Test individual MCDC functionality"""
    
    def test_mcdc_creation(self):
        """Test MCDC instantiation"""
        loc = MCDCLocation(
            location_id="M-1",
            region=DeploymentRegion.ASIA_PACIFIC,
            latitude=1.3521,
            longitude=103.8198,
            city="Singapore",
            country="Singapore"
        )
        mcdc = MobileContainerDC(
            mcdc_id="sg_mcdc",
            location=loc,
            num_fpgas=500
        )
        
        assert mcdc.mcdc_id == "sg_mcdc"
        assert mcdc.num_fpgas == 500
        assert mcdc.uptime_sla_pct == 99.95
    
    def test_mcdc_power_cost(self):
        """Test MCDC power cost calculation"""
        loc = MCDCLocation("M", DeploymentRegion.NORTH_AMERICA, 0, 0, "Test", "Test")
        mcdc = MobileContainerDC(
            mcdc_id="test",
            location=loc,
            power_consumption_kw=400.0
        )
        
        cost = mcdc.get_power_cost()
        # ~$0.15/kWh × 400 kW × 8760 h/year
        expected = 400.0 * 0.15 * 8760 / 1000000
        assert abs(cost - expected) < 0.001
    
    def test_mcdc_summary(self):
        """Test MCDC summary output"""
        loc = MCDCLocation(
            location_id="S",
            region=DeploymentRegion.EUROPE,
            latitude=48.8566,
            longitude=2.3522,
            city="Paris",
            country="France"
        )
        mcdc = MobileContainerDC(
            mcdc_id="paris_1",
            location=loc,
            num_fpgas=500
        )
        
        summary = mcdc.get_summary()
        assert summary['mcdc_id'] == "paris_1"
        assert summary['location']['city'] == "Paris"
        assert summary['num_fpgas'] == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
