#!/bin/bash

# deploy.sh - Deployment script for Project

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly DEPLOY_LOG="${PROJECT_ROOT}/logs/deploy.log"
readonly CONFIG_FILE="${PROJECT_ROOT}/config/deploy.conf"
readonly BACKUP_DIR="${PROJECT_ROOT}/backups"
readonly TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Default configuration
DEPLOY_ENV="production"
DRY_RUN=false
FORCE_DEPLOY=false
SKIP_BACKUP=false
VERBOSE=false

# Load configuration file if exists
load_config() {
    if [[ -f "${CONFIG_FILE}" ]]; then
        source "${CONFIG_FILE}"
    fi
}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') $*" >> "${DEPLOY_LOG}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') $*" >> "${DEPLOY_LOG}"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
    echo "[WARNING] $(date '+%Y-%m-%d %H:%M:%S') $*" >> "${DEPLOY_LOG}"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $*" >> "${DEPLOY_LOG}"
}

# Print usage information
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Deployment script for Project

Options:
    -e, --env ENVIRONMENT   Deployment environment (production, staging, development)
                            Default: production
    -d, --dry-run           Perform a dry run without making changes
    -f, --force             Force deployment without confirmation
    -s, --skip-backup       Skip backup of current deployment
    -v, --verbose           Enable verbose output
    -h, --help              Show this help message

Examples:
    $(basename "$0") -e staging
    $(basename "$0") --dry-run --verbose
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--env)
                DEPLOY_ENV="$2"
                shift 2
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -f|--force)
                FORCE_DEPLOY=true
                shift
                ;;
            -s|--skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Validate deployment environment
validate_environment() {
    case "${DEPLOY_ENV}" in
        production|staging|development)
            log_info "Deploying to ${DEPLOY_ENV} environment"
            ;;
        *)
            log_error "Invalid environment: ${DEPLOY_ENV}"
            log_error "Valid environments: production, staging, development"
            exit 1
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if running as root (if needed)
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root user"
    fi
    
    # Check required directories
    local required_dirs=("logs" "backups" "config")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "${PROJECT_ROOT}/${dir}" ]]; then
            log_info "Creating directory: ${PROJECT_ROOT}/${dir}"
            mkdir -p "${PROJECT_ROOT}/${dir}"
        fi
    done
    
    # Initialize log file
    touch "${DEPLOY_LOG}"
    
    log_success "Prerequisites check completed"
}

# Backup current deployment
backup_current() {
    if [[ "${SKIP_BACKUP}" == true ]]; then
        log_warning "Skipping backup as requested"
        return 0
    fi
    
    log_info "Creating backup of current deployment..."
    
    local backup_path="${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz"
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "[DRY RUN] Would create backup: ${backup_path}"
        return 0
    fi
    
    # Create backup of current deployment (excluding logs, backups, and config)
    if tar -czf "${backup_path}" \
        --exclude="logs" \
        --exclude="backups" \
        --exclude="config/deploy.conf" \
        -C "${PROJECT_ROOT}" . 2>/dev/null; then
        log_success "Backup created: ${backup_path}"
        
        # Clean up old backups (keep last 5)
        find "${BACKUP_DIR}" -name "backup_*.tar.gz" -type f | \
            sort -r | \
            tail -n +6 | \
            xargs rm -f 2>/dev/null || true
    else
        log_error "Failed to create backup"
        return 1
    fi
}

# Load environment-specific configuration
load_environment_config() {
    local env_config="${PROJECT_ROOT}/config/${DEPLOY_ENV}.conf"
    
    if [[ -f "${env_config}" ]]; then
        log_info "Loading environment configuration: ${env_config}"
        source "${env_config}"
    else
        log_warning "No environment-specific configuration found: ${env_config}"
    fi
}

# Perform pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check disk space
    local available_space=$(df -k "${PROJECT_ROOT}" | awk 'NR==2 {print $4}')
    if [[ ${available_space} -lt 1048576 ]]; then  # Less than 1GB
        log_warning "Low disk space available: $((available_space / 1024))MB"
    fi
    
    # Check for running processes (example)
    if pgrep -f "project_main" >/dev/null; then
        log_info "Found running project processes"
    fi
    
    log_success "Pre-deployment checks completed"
}

# Stop services
stop_services() {
    log_info "Stopping services..."
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "[DRY RUN] Would stop services"
        return 0
    fi
    
    # Add service stopping logic here
    # Example: systemctl stop project-service
    
    log_success "Services stopped"
}

# Deploy new version
deploy_new_version() {
    log_info "Deploying new version..."
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "[DRY RUN] Would deploy new version"
        return 0
    fi
    
    # Add deployment logic here
    # Example: rsync, git pull, copy files, etc.
    
    log_success "New version deployed"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "[DRY RUN] Would run database migrations"
        return 0
    fi
    
    # Add migration logic here
    # Example: alembic upgrade head
    
    log_success "Database migrations completed"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "[DRY RUN] Would start services"
        return 0
    fi
    
    # Add service starting logic here
    # Example: systemctl start project-service
    
    log_success "Services started"
}

# Run post-deployment tests
post_deployment_tests() {
    log_info "Running post-deployment tests..."
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "[DRY RUN] Would run post-deployment tests"
        return 0
    fi
    
    # Add test logic here
    # Example: curl health check, smoke tests
    
    log_success "Post-deployment tests completed"
}

# Cleanup temporary files
cleanup() {
    log_info "Cleaning up temporary files..."
    
    # Add cleanup logic here
    
    log_success "Cleanup completed"
}

# Main deployment function
main_deployment() {
    log_info "Starting deployment to ${DEPLOY_ENV} environment"
    log_info "Timestamp: ${TIMESTAMP}"
    log_info "Project root: ${PROJECT_ROOT}"
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_warning "DRY RUN MODE - No changes will be made"
    fi
    
    # Ask for confirmation unless forced
    if [[ "${FORCE_DEPLOY}" == false ]] && [[ "${DRY_RUN}" == false ]]; then
        echo -e "${YELLOW}Are you sure you want to deploy to ${DEPLOY_ENV}? (y/N)${NC}"
        read -r response
        if [[ ! "${response}" =~ ^[Yy]$ ]]; then
            log_info "Deployment cancelled by user"
            exit 0
        fi
    fi
    
    # Execute deployment steps
    check_prerequisites
    backup_current
    load_environment_config
    pre_deployment_checks
    stop_services
    deploy_new_version
    run_migrations
    start_services
    post_deployment_tests
    cleanup
    
    log_success "Deployment completed successfully!"
    
    # Final summary
    cat << EOF

╔══════════════════════════════════════╗
║         DEPLOYMENT COMPLETE          ║
╠══════════════════════════════════════╣
║ Environment: ${DEPLOY_ENV}
║ Timestamp:   ${TIMESTAMP}
║ Status:      SUCCESS
║ Log file:    ${DEPLOY_LOG}
╚══════════════════════════════════════╝

EOF
}

# Error handler
error_handler() {
    local exit_code=$?
    local error_line=$1
    
    log_error "Deployment failed on line ${error_line} with exit code ${exit_code}"
    log_error "Check log file for details: ${DEPLOY_LOG}"
    
    # Attempt to restore from backup if deployment failed
    if [[ "${SKIP_BACKUP}" == false ]] && [[ "${DRY_RUN}" == false ]]; then
        log_info "Attempting to restore from backup..."
        # Add restore logic here if needed
    fi
    
    exit ${exit_code}
}

# Set error trap
trap 'error_handler ${LINENO}' ERR

# Main execution
main() {
    # Parse command line arguments
    parse_args "$@"
    
    # Load configuration
    load_config
    
    # Validate environment
    validate_environment
    
    # Run main deployment
    main_deployment
}

# Run main function with all arguments
main "$@"