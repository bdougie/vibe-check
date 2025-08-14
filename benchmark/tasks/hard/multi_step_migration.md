# Task: Multi-Step Data Migration

**Difficulty**: Hard  
**Repo**: Your current project  
**Issue**: Migrate benchmark results from old format to new schema with validation  

## Current Situation
Old results use inconsistent formats:
- Some use JSON, others use CSV
- Field names vary across versions
- Missing data in some records
- Nested structures need flattening

## Requirements
- Implement a robust multi-step migration pipeline
- Support multiple input formats (JSON, CSV)
- Handle schema versioning and evolution
- Provide comprehensive validation at each step
- Maintain data integrity throughout the process
- Create detailed audit logs
- Implement rollback capability

## Migration Steps Required
1. **Discovery Phase**
   - Scan all result files
   - Identify format versions
   - Document inconsistencies
   - Create migration plan

2. **Validation Phase**
   - Validate source data integrity
   - Check for required fields
   - Identify corrupt records
   - Generate pre-migration report

3. **Transformation Phase**
   - Normalize field names
   - Convert data types
   - Flatten nested structures
   - Handle missing values

4. **Migration Phase**
   - Backup original data
   - Apply transformations
   - Validate transformed data
   - Write to new format

5. **Verification Phase**
   - Compare row counts
   - Verify data integrity
   - Check constraint violations
   - Generate migration report

## Data Challenges
- Dates in multiple formats (ISO, Unix timestamp, strings)
- Numeric fields sometimes stored as strings
- Boolean values as 1/0, true/false, yes/no
- Arrays stored as comma-separated strings
- Missing required fields need defaults

## Schema Evolution
Version 1: Simple flat structure
Version 2: Added nested metrics
Version 3: Introduced relationships
Version 4: Current target schema

## Expected Outcome
- All data successfully migrated
- No data loss or corruption
- Comprehensive audit trail
- Rollback capability
- Performance metrics tracked

**Time Estimate**: 60-90 minutes

## Success Criteria
- [ ] Correctly identifies all format versions
- [ ] Handles all edge cases
- [ ] Maintains data integrity
- [ ] Provides detailed migration report
- [ ] Supports incremental migration
- [ ] Includes rollback mechanism