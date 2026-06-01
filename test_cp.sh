#!/bin/bash
mkdir -p mock_frontend/dist
mkdir -p mock_backend

# Simulate the buildCommand
cd mock_frontend && echo "building..." && \
cp -r mock_frontend/dist mock_backend/frontend_dist || echo "CP FAILED"
