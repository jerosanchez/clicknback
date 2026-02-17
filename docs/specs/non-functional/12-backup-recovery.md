# NFR-12: Data Backup & Disaster Recovery

## Overview

The system must have robust backup and recovery procedures to protect against data loss due to hardware failure, corruption, or disasters, ensuring business continuity and regulatory compliance.

## Motivation

Data is the core asset of a financial system. Loss of transaction history, wallet states, or user data is catastrophic. Backups and recovery procedures are essential for compliance (e.g., SOC 2) and operational resilience.

## Definition

- Automated backups are created at regular intervals and tested for recoverability.
- Backups are stored in geographically distinct locations (e.g., different AWS regions).
- Recovery procedures are documented and tested; RTO and RPO are defined and met.
- Backup encryption and access controls prevent unauthorized recovery.

## Acceptance Criteria

- Full database backup is created daily; point-in-time recovery is possible within 24 hours.
- Recovery Point Objective (RPO): data loss < 1 hour.
- Recovery Time Objective (RTO): recover to full operational state within 4 hours.
- Backup integrity is verified weekly with test recoveries to a non-production environment.
- Disaster recovery runbook is documented and reviewed quarterly.

## Technical Approach

- Automated backups via PostgreSQL `pg_basebackup` or managed service (AWS RDS automated backups).
- Continuous WAL (Write-Ahead Logs) archiving for point-in-time recovery.
- Cross-region replication for high availability: standby database ready to takeover.
- Backup encryption using service-managed or externally-managed keys (never unencrypted).
- Quarterly disaster recovery drills: restore production backup to staging, verify full functionality.
- Backup retention policy: 30 days of daily backups, 1 year of weekly backups.
- Monitoring: alert if backup fails or verification detects corruption.
