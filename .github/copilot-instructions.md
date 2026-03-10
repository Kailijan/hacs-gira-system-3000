# General instructions for the repository

This repository contains custom components for Home Assistant, specifically for the Gira System 3000. The code is organized into different files based on the type of entity (e.g., cover, light, sensor). Each file contains the necessary logic to integrate the respective entities with Home Assistant.

When contributing to this repository, please ensure that your code follows the existing style and conventions. This includes using appropriate logging, defining configuration schemas where necessary, and adhering to Home Assistant's best practices for custom components.

## Language and Style

- Use english for all code comments and documentation
- Refer to Home Assistant's developer documentation for guidance on best practices and coding standards: https://developers.home-assistant.io/docs/creating_component_index

## Deployment

The custom components in this reposiory can be deployed to a Home Assistant instance using HACS (Home Assistant Community Store).
Please respect the HACS guidelines for custom components when making contributions: https://hacs.xyz/docs/publish/

## Local testing

The project contains a devcontainer for running a containerized instance of Home Assistant.