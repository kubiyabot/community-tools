# Crossplane Tools for Kubiya

This module provides a comprehensive set of tools for managing Crossplane operations through Kubiya. It includes functionality for managing Crossplane core operations, providers, compositions, claims, and packages.

## Components

### Core Operations
- Install and uninstall Crossplane
- Manage Crossplane system status
- Version management

### Provider Management
- Install and configure providers
- Manage provider lifecycle
- Monitor provider status

### Composition Management
- Create and manage compositions
- Handle Composite Resource Definitions (XRDs)
- Composition versioning and updates

### Claim Management
- Create and manage composite resource claims
- Monitor claim status
- Handle claim lifecycle

### Package Management
- Install and manage Crossplane packages
- Package repository management
- Package updates and versioning

## Installation

```bash
pip install -e .
```

## Usage

### Basic Usage

```python
from crossplane_tools.tools import CoreOperations

# Initialize the core operations
core = CoreOperations()

# Install Crossplane
core.install_crossplane()

# Check Crossplane status
core.get_status()
```

### Provider Management

```python
from crossplane_tools.tools import ProviderManager

# Initialize the provider manager
provider_mgr = ProviderManager()

# Install a provider
provider_mgr.install_provider(provider_package="crossplane/provider-aws:v0.24.1")

# Configure the provider
provider_mgr.configure_provider(provider_config="path/to/config.yaml")
```

### Composition Management

```python
from crossplane_tools.tools import CompositionManager

# Initialize the composition manager
comp_mgr = CompositionManager()

# Apply a composition
comp_mgr.apply_composition(composition_file="path/to/composition.yaml")

# List all compositions
comp_mgr.list_compositions()
```

### Claim Management

```python
from crossplane_tools.tools import ClaimManager

# Initialize the claim manager
claim_mgr = ClaimManager()

# Create a claim
claim_mgr.apply_claim(claim_file="path/to/claim.yaml")

# Monitor claim status
claim_mgr.watch_claim_status(
    claim_name="my-claim",
    claim_type="database.example.org",
    namespace="default"
)
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. 