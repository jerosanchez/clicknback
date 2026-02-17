# Operation Plan

## 1. Overview

Operational strategy for ClickNBack, demonstrating awareness of production runtime concerns while maintaining pragmatism for a demo system. The strategy balances minimal viable operations with enough observability to understand system behavior and recover from incidents gracefully.

### 1.1 Operational Philosophy

**Minimal Viable Operations:** Implement only the operational practices that prevent data loss, enable quick problem diagnosis, and allow graceful recovery. Heavy instrumentation and alerting are deferred until scale demands justify the complexity.

**Observability Over Monitoring:** Collect enough data to understand system behavior when needed (logs, health endpoints), but avoid real-time metric dashboards and alert fatigue in a demo context.

**Known State:** Maintain clear documentation of system state, deployment versions, and rollback procedures so issues can be addressed methodically rather than reactively.

---

## 2. Health & Availability

### 2.1 Health Check Endpoints

Application exposes liveness and readiness probes:

- `/health/live` — Service is running (responds 200 if process alive)
- `/health/ready` — Service is ready to serve requests (includes database connectivity check)

**Purpose:** Enables deployment systems and ops teams to detect unhealthy instances quickly. Used during deployments to verify successful startup.

### 2.2 Recovery Procedures

**Database Unavailable:** Application containers restart automatically. If database remains down, manual intervention required (check VPS logs, verify PostgreSQL container status).

**Application Crash:** Container orchestration (Docker) restarts service. If crashes persist, review application logs to identify root cause.

**Full System Failure:** Manual VPS restart. Once online, Docker starts containers automatically; database containers verify data integrity on startup.

---

## 3. Data Management

### 3.1 Database Backups

**Local Development:** Not backed up (ephemeral).

**Production:** Weekly automated backups to external storage (e.g., AWS S3, DigitalOcean Spaces). Retention: 4 weeks.

**Backup Verification:** Monthly test restore to verify backup integrity. Document restore procedure.

**Rationale:** Protects against data loss (accidental deletion, corruption, ransomware). Weekly frequency balances recovery window against storage cost for a demo system.

### 3.2 Database Maintenance

**Schema Migrations:** Applied automatically during deployment via Alembic. Each deployment tracks applied migrations in database history table.

**Data Integrity:** Application enforces constraints at database level (foreign keys, unique indexes). Periodic integrity checks via `REINDEX` and `ANALYZE` (monthly during maintenance window).

**Replication (Future):** If scale increases, consider read replicas for failover capability. Not implemented initially.

---

## 4. Logging & Diagnostics

### 4.1 Application Logging

Application logs structured events to stdout:

- Request start/completion with response status and latency
- Authentication failures (count, not credentials)
- Business logic warnings (expired offers attempted, balance mismatches)
- Error stack traces with request context

**Access:** Logs captured by container runtime (Docker) and accessible via `docker logs <container>` or centralized log aggregation (optional future enhancement).

### 4.2 Log Retention

**Local:** In-memory buffer and Docker log files (default retention ~2 weeks depending on log volume).

**Production:** Centralized logging service recommended (Papertrail, CloudWatch) with 30-day retention. For MVP, logs shipped to file on VPS with manual archival.

### 4.3 Diagnostics

On-demand inspection endpoints (optional):

- `/debug/database-stats` — Connection pool status, query count (development only, restricted by auth in production)
- `/debug/version` — Current deployed version, commit hash

**Access:** Available to authorized admin users only. Used during incident investigation.

---

## 5. Incident Response

### 5.1 Problem Classification

**Severity 1 (Critical):** System unavailable, data inaccessible. Example: Database down, all containers crashed.

- Response: Immediate restart/recovery attempt
- Escalation: Manual investigation if restart fails

**Severity 2 (High):** Specific features broken, system partially operational. Example: User registration failing, auth service degraded.

- Response: Isolate affected endpoint, review recent logs, identify code/config change
- Escalation: If unresolved in 10 minutes, rollback to previous version

**Severity 3 (Low):** Degraded performance, minor feature issues. Example: Response times elevated, occasional timeouts.

- Response: Monitor, collect logs for analysis, investigate during next maintenance window

### 5.2 Rollback Procedure

Versioned deployments enable quick rollback:

1. Identify last known good version (review git tags, deployment history)
2. Redeploy that version: `git checkout v0.1.0 && docker-compose up -d`
3. Verify health checks return 200
4. Alert team; post-incident review to identify root cause

**Target Time:** < 5 minutes from decision to rollback complete

---

## 6. Maintenance & Updates

### 6.1 Maintenance Windows

**Frequency:** First Sunday of each month, 2:00-3:00 AM UTC (outside typical usage hours).

**Activities:**

- Database maintenance (`VACUUM`, `ANALYZE`)
- Log archival
- Dependency updates (security patches, minor version upgrades)
- Backup verification test
- Documentation updates

### 6.2 Security Updates

**Critical vulnerabilities:** Applied immediately outside maintenance window.

**High/Low:** Batched into next maintenance window.

**Tracking:** Subscribe to security advisories for Python dependencies (e.g., GitHub security alerts).

### 6.3 Dependency Management

Python dependencies specified in `pyproject.toml` with pinned versions. Monthly review:

- Check for security patches
- Evaluate minor/major version updates
- Test upgrades in local environment before production deployment

Database version managed via Docker image tag. Upgrades tested in staging environment first (or local docker-compose).

---

## 7. Performance & Capacity

### 7.1 Performance Baseline

Establish baseline metrics (without third-party monitoring):

- **API Response Time:** Target p99 < 200ms for typical requests (measured via application logs)
- **Database Query Time:** Slow queries logged if > 1000ms (via application instrumentation or PostgreSQL slow query log)
- **Container Resource Usage:** Reviewed monthly via `docker stats` (CPU, memory utilization)

**Monitoring:** Baseline checks performed manually during maintenance windows or when performance issues reported.

### 7.2 Scaling (Future Consideration)

Current single-instance deployment handles thousands of requests/day without scaling concerns. If traffic increases:

- Implement horizontal scaling: Multiple application instances behind load balancer
- Add read replicas for database (PostgreSQL replication)
- Implement caching layer (Redis) for frequently accessed data
- Centralized monitoring and alerting becomes necessary at that point

---

## 8. Documentation & Runbooks

### 8.1 Critical Documentation

- **Deployment procedure:** How to release a new version (git tag, GitHub Actions, confirmation steps)
- **Rollback procedure:** How to revert to previous version (measured < 5 minutes)
- **Database recovery:** How to restore from backup, verify integrity
- **Health check URLs:** How to validate system is operational post-deployment
- **Common issues:** Known problems and resolutions (e.g., "If database connection time out, restart Docker daemon")

Documentation stored in `/docs` alongside code, updated with each operational incident or procedure change.

### 8.2 On-Call Handoff

If running with on-call rotation:

- Current production version and deployment date
- Recent incidents and resolutions
- Known issues or degradations
- Maintenance window schedule
- Contact information for escalation (infrastructure provider support, team members)

---

## 9. Disaster Recovery & Business Continuity

### 9.1 Recovery Time Objectives (RTO)

- **Full system failure:** 1 hour (manual intervention to restart VPS + containers)
- **Database corruption:** 4 hours (restore from weekly backup, verify data, redeploy)
- **Application bug causing data loss:** 24 hours (detect issue, investigate, apply fix, restore backup if necessary)

### 9.2 Recovery Point Objective (RPO)

- **Data loss tolerance:** 7 days (weekly backup retention). In case of catastrophic failure, accept up to 1 week of lost data.

### 9.3 Tested Procedures

- Monthly test: Restore database from backup to verify integrity and procedure documentation accuracy
- Quarterly: Conduct full failover test (restart VPS, verify application and data recovered correctly)

---

## 10. Team Responsibilities & Escalation

### 10.1 Day-to-Day

**Developer:** Deploys changes, resolves application-level issues, reviews logs for errors.

**Ops (Initially: Developer):** Monitors system health, verifies backups, handles infrastructure issues (VPS provider support).

### 10.2 Escalation Path

1. **Application Issue:** Developer investigates; if unresolved in 15 min, roll back to previous version
2. **Infrastructure Issue:** Check VPS provider status page; contact support if needed
3. **Database Issue:** Review PostgreSQL logs; if unresolved, restore from backup during maintenance window
