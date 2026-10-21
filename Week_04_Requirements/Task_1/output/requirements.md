# Software Requirements Specification

*System under specification:* These requirements describe a consortium-scale integrated library system and management reporting platform. The system supports multi-branch collection, circulation, patron, financial, transfer, audit, accessibility, security, data-quality, and historical reporting workflows.

*Generated:* 2026-10-21 18:49 UTC by a LangGraph agentic network (extraction: gpt-5.6-luna, consolidation: gpt-5.6-luna, adjudication: gpt-5-mini, review: gpt-6-luna)
*Source corpus:* 20 documents

## 1. Priority scale

| Priority | Meaning |
|---|---|
| **P1** | Must have - critical for core operation, legal/audit compliance, or data integrity; blocking for the first release. |
| **P2** | Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible. |
| **P3** | Could have - valuable enhancement; schedule when capacity allows. |
| **P4** | Later - nice-to-have or speculative; keep in the backlog. |

## 2. Glossary (consistent terminology)

| Term | Definition |
|---|---|
| ILS | Integrated library system supporting library collections, patrons, circulation, financial activity, and reporting. |
| OPAC | Online Public Access Catalog used by patrons to search library holdings and perform supported account activities. |
| material volume | The quantity of library materials reported by library, category, status, or period. |
| capacity | A branch's ability to hold or process materials, represented by measures such as shelf space, limits, or item counts. |
| shelf space utilization | The amount or percentage of available shelf capacity occupied by library materials. |
| transfer | The movement or reassignment of an item between branches or other library locations. |
| in-transit item | An item currently moving between library locations. |
| purge | The controlled identification and deletion of records meeting configured removal criteria. |
| last copy | The only remaining copy within a selected library, system, or consortium scope. |
| deletion audit | A persistent record of deletion events and associated record, user, location, and time information. |
| uncataloged material | Library material tracked or circulated without a complete catalog record. |
| report template | A reusable report definition containing query, filter, and display settings. |
| canned report | A predefined report template with a fixed purpose and configurable parameters. |
| ad hoc report | A report created or run for a specific user-defined information need. |
| report queue | An ordered set of report jobs awaiting or undergoing processing, with status and position information. |
| reporting warehouse | A data store preserving historical or consolidated data for reporting and analysis. |
| MARC | Machine-Readable Cataloging format used to encode bibliographic record fields. |
| authority record | A controlled record used to maintain standardized names, subjects, or other catalog access points. |
| security group | A named collection of users used to assign shared rights and privileges. |
| assistive technology | Software or hardware that helps people with disabilities use the system. |
| cross-tabulation | Analysis grouping activity across multiple dimensions such as branch, terminal, time, or patron attributes. |
| transaction archive | A retained historical record of transactions subject to retention and privacy controls. |
| Section 508 | U.S. accessibility requirements for electronic and information technology. |
| USMARC21 | A standard machine-readable bibliographic data exchange format. |
| EDIFACT | A standard electronic data interchange format for structured business data. |
| ARIA | Accessible Rich Internet Applications attributes that improve access for assistive technology users. |
| pivot table | A report format that summarizes and rearranges data across selected dimensions. |

## 3. Requirements overview

| ID | Name | Priority | Area | Sources |
|---|---|---|---|---|
| REQ-001 | Material volume reporting | P2 | collection reporting | D01, D07, D10, D11, D12, D14, D15, D19, D20 |
| REQ-002 | Material status counts | P2 | collection reporting | D01, D10, D14, D20 |
| REQ-003 | Branch capacity overview | P2 | branch capacity | D02, D10 |
| REQ-004 | Branch capacity filtering | P3 | branch capacity | D02 |
| REQ-005 | Shelf space analysis | P2 | collection analysis | D03, D10, D14, D15 |
| REQ-006 | Collection comparison views | P3 | collection analysis | D03 |
| REQ-007 | Transfer candidate selection | P2 | item transfers | D04, D10, D15, D20 |
| REQ-008 | Transfer location updates | P2 | item transfers | D04, D10, D15, D20 |
| REQ-009 | Transfer preview confirmation | P1 | item transfers | D04 |
| REQ-010 | Batch transfer processing | P1 | item transfers | D04 |
| REQ-011 | Transfer logistics outputs | P2 | item transfers | D04, D06, D10, D15 |
| REQ-012 | Transfer history and reversion | P1 | item transfers | D04, D10, D15, D20 |
| REQ-013 | Transit item reporting | P2 | circulation reporting | D05, D10, D14, D15 |
| REQ-014 | Missing damaged reporting | P2 | condition reporting | D05, D10, D15, D18 |
| REQ-015 | Purge candidate criteria | P2 | record purging | D06, D10, D15 |
| REQ-016 | Purge review and last copies | P2 | record purging | D06, D10, D14, D15 |
| REQ-017 | Controlled purge execution | P2 | record purging | D06, D07, D20 |
| REQ-018 | Deletion audit reporting | P1 | deletion auditing | D07, D14, D15 |
| REQ-019 | Patron demographic reporting | P2 | patron reporting | D08, D10, D14 |
| REQ-020 | Patron age calculation | P2 | patron reporting | D08, D10, D12 |
| REQ-021 | Inactive patron reporting | P2 | inactive patrons | D09, D10, D17 |
| REQ-022 | Inactive patron exclusions | P2 | inactive patrons | D09 |
| REQ-023 | Inactive patron processing | P2 | inactive patrons | D09, D16, D18 |
| REQ-024 | Electronic activity definition | P2 | inactive patrons | D09 |
| REQ-025 | Query construction | P2 | querying | D10, D12 |
| REQ-026 | Role-based access control | P1 | access control | D04, D10, D12, D13, D16, D17, D18, D19 |
| REQ-027 | Staff authentication | P1 | authentication | D10, D13, D18 |
| REQ-028 | Report authoring | P2 | report authoring | D10, D12, D13, D14, D17, D18, D19, D20 |
| REQ-029 | Report safeguards | P1 | report security | D10, D11, D12 |
| REQ-030 | Report filtering | P2 | report filtering | D10, D14, D19, D20 |
| REQ-031 | Report output formats | P2 | report output | D10, D14, D19, D20 |
| REQ-032 | Report result context | P2 | report results | D10, D12, D14, D19, D20 |
| REQ-033 | Report execution queue | P2 | report processing | D10, D12, D14, D18, D19, D20 |
| REQ-034 | Report scheduling and delivery | P2 | report distribution | D10, D14, D20 |
| REQ-035 | Report diagnostics | P2 | error handling | D10, D18, D19 |
| REQ-036 | Accessible user interfaces | P1 | accessibility | D10, D14, D16, D18, D19 |
| REQ-037 | Accessible HTML output | P1 | accessibility | D10, D16, D20 |
| REQ-038 | Supported client platforms | P2 | deployment | D10, D16, D18 |
| REQ-039 | Environment management | P2 | environment management | D10, D14, D16, D19 |
| REQ-040 | Historical reporting | P2 | historical reporting | D10, D14, D19, D20 |
| REQ-041 | Reporting performance isolation | P1 | performance | D10, D14, D16, D19, D20 |
| REQ-042 | Data specifications | P2 | data management | D10, D18, D19 |
| REQ-043 | Bibliographic authority control | P2 | bibliographic control | D10, D16, D18, D19 |
| REQ-044 | Enterprise ILS integration | P2 | system integration | D10, D18, D19 |
| REQ-045 | Read-only reporting access | P2 | data access | D10, D14, D16, D18, D19 |
| REQ-046 | Uncataloged inventory tracking | P2 | uncataloged materials | D10, D15, D17 |
| REQ-047 | Uncataloged material processing | P2 | uncataloged materials | D10, D15 |
| REQ-048 | Item status conversion | P2 | item maintenance | D06, D10, D15 |
| REQ-049 | Empty record deletion | P2 | record maintenance | D06, D10, D15 |
| REQ-050 | Circulation transaction reporting | P2 | circulation reporting | D10, D12, D20 |
| REQ-051 | Circulation dimension analysis | P3 | circulation analytics | D10, D14, D20 |
| REQ-052 | Collection metrics reporting | P3 | collection analytics | D10, D14 |
| REQ-053 | Financial reporting | P2 | financial reporting | D10, D11, D14 |
| REQ-054 | Payment traceability | P1 | financial services | D10, D11 |
| REQ-055 | Financial retention and privacy | P1 | data retention | D10, D11, D12, D17, D20 |
| REQ-056 | Management analytics | P2 | management reporting | D10, D17, D18 |
| REQ-057 | Consortium-scale operation | P1 | capacity | D10, D18 |
| REQ-058 | Online help | P2 | help | D10, D14, D16, D18, D19 |
| REQ-059 | Staff and operational reports | P2 | reporting | D10, D12, D18, D20 |
| REQ-060 | Data quality reporting | P2 | data quality | D10, D14, D15, D18 |
| REQ-061 | Report documentation | P2 | documentation | D10, D17, D18, D19 |
| REQ-062 | Relational data backend | P2 | architecture | D10, D16 |
| REQ-063 | Report the number of board books | P3 | general | D01 |
| REQ-064 | Allow transactions to be queried either collectively or by transaction | P3 | general | D10 |
| REQ-065 | Provide a list of patrons who are barred | P3 | general | D10 |
| REQ-066 | Provide a report of IntraPINES loans by facility | P3 | general | D10 |
| REQ-067 | Provide monthly counts of noncataloged in-house use | P3 | general | D10 |
| REQ-068 | Show when a report was submitted | P3 | general | D12 |
| REQ-069 | Provide hover tooltips for report titles | P3 | general | D14 |
| REQ-070 | Group transactions by hour | P3 | general | D20 |
| REQ-071 | Support program attendance tracking reports | P3 | general | D20 |

## 4. Requirements

### Area: access control

#### REQ-026: Role-based access control

**Priority:** P1 — Must have - critical for core operation, legal/audit compliance, or data integrity; blocking for the first release.

The system shall manage access through security groups and role profiles for staff, local administrators, global administrators, individuals, workgroups, and arbitrary staff groups. Changing a role assignment shall propagate the associated permissions, including report, folder, filter, display-field, query, and configuration permissions.

**Sources:**

- `D13` Staff login difficulties - need for streamlined access — "This would allow access control for individuals, workgroups, and arbitrary staff groups."
- `D12` Report features and interface requirements — "and display fields can be altered."
- `D04` Moving items between branches - utility needed — "limited to certain roles (managers, administrators, transfer coordinators)"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "allow access control for individuals, workgroups, and arbitrary staff groups"
- `D16` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "access control for individuals, workgroups, and arbitrary staff groups"
- `D17` PINES REPORTS WORKING GROUP - FIRST MEETING MINUTES — "generating statistical reports for PINES as a whole"
- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "through which all new Reports development would be filtered"
- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "We need security groups and/or 'roles' that allow access control"

**Keywords:** roles, permissions, security groups, authorization

### Area: accessibility

#### REQ-036: Accessible user interfaces

**Priority:** P1 — Must have - critical for core operation, legal/audit compliance, or data integrity; blocking for the first release.

User-facing interfaces shall comply with applicable accessibility requirements, including Section 508 where applicable. Reporting creation, execution, results, administration, and help shall work with assistive technologies.

**Sources:**

- `D16` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "We MUST comply with Section 508 accessibility requirements"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "No accessibility support for report interface"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "other assistive technology programs designed to increase accessibility"
- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "other software programs designed to increase accessibility"
- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "The help system needs to work with screen readers"

**Keywords:** accessibility, section 508, screen readers, interfaces

#### REQ-037: Accessible HTML output

**Priority:** P1 — Must have - critical for core operation, legal/audit compliance, or data integrity; blocking for the first release.

The system shall produce standards-compliant semantic HTML for user interfaces and report output. HTML shall provide appropriate alternative text and ARIA labels for assistive-technology users.

**Sources:**

- `D16` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "The HTML output needs to be properly structured with alt tags"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "produce standards-compliant HTML output for web-based components"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "I can't find the reports I need"

**Keywords:** html, semantic, aria, alt text

### Area: architecture

#### REQ-062: Relational data backend

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall use a fully relational database backend and support complex joins across related records. Reporting shall remain compatible with the enterprise relational structure.

**Sources:**

- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "use a fully relational database back-end"
- `D16` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "I'd prefer to keep everything in the main relational database"

**Keywords:** relational database, joins, backend, reporting

### Area: authentication

#### REQ-027: Staff authentication

**Priority:** P1 — Must have - critical for core operation, legal/audit compliance, or data integrity; blocking for the first release.

The system shall support individual username-and-password authentication and optional card or badge login. Card-based login shall identify the individual but shall not bypass individual authentication, and the authenticated staff member shall be recorded for audit purposes.

**Sources:**

- `D13` Staff login difficulties - need for streamlined access — "the card is just a convenient way to identify the person, but it shouldn't bypass individual authentication entirely."
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "traditional username/password should also be available as a fallback"
- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "Staff login needs (card swipe)"

**Keywords:** authentication, passwords, badges, staff

### Area: bibliographic control

#### REQ-043: Bibliographic authority control

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system documentation shall describe bibliographic record import and export and validation against internal and external authority sources. The documentation shall explain how authority sources are used.

**Sources:**

- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "validation of bibliographic records against internal and external authority sources"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "validation of bibliographic records against internal and external authority sources"
- `D16` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "export/import functionality for report templates"
- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "Validation of bibliographic records against internal and external authority sources"

**Keywords:** bibliographic, authority, validation, import

### Area: branch capacity

#### REQ-003: Branch capacity overview

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall show capacity information for all branches and allow users to inspect an individual branch. Capacity views shall support defined metrics, trends, and indicators for under-capacity, nearing-capacity, and over-capacity locations.

**Sources:**

- `D02` Can we see all branches at once? — "color-coding - green for under capacity, yellow for getting full, red for at/over capacity"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "The system should provide an interface showing the capacity of all branches"

**Keywords:** branches, capacity, trends, indicators

#### REQ-004: Branch capacity filtering

**Priority:** P3 — Could have - valuable enhancement; schedule when capacity allows.

Users shall be able to sort and filter branch capacity information by region, library type, and current load. The resulting information shall be exportable to CSV.

**Sources:**

- `D02` Can we see all branches at once? — "sort and filter. By region, by library type, by current load"

**Keywords:** capacity filters, regions, sorting, csv

### Area: capacity

#### REQ-057: Consortium-scale operation

**Priority:** P1 — Must have - critical for core operation, legal/audit compliance, or data integrity; blocking for the first release.

The system shall support consortium operations across 286 locations, approximately 17 million annual circulations, and purchasing and processing of more than 900,000 items per year.

**Sources:**

- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "purchasing and processing over 900,000 items per year"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "support a library consortium with 286 locations, 17 million annual circulations"

**Keywords:** consortium, locations, circulation, capacity

### Area: circulation analytics

#### REQ-051: Circulation dimension analysis

**Priority:** P3 — Could have - valuable enhancement; schedule when capacity allows.

The system shall report circulation by patron age, county, home library, circulation modifier, category fields, Dewey classification, MARC data, and shelving location. Users shall be able to select applicable dimensions.

**Sources:**

- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "Circulation Count by Circ Location broken down by Patron Home Library"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "Circulation Count by Age Demographic (not available)"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "Need to pull specific MARC fields but they're spread across multiple rows"

**Keywords:** circulation, dimensions, demographics, classification

### Area: circulation reporting

#### REQ-013: Transit item reporting

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall provide consolidated reports for items traveling to and from locations. Reports shall support branch and system scopes, due-date sorting, sending and destination libraries, and configurable long-transit thresholds.

**Sources:**

- `D05` Missing and damaged items - we need a report — "can we sort by due date?"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "items that have been in-transit for more than X days (X configurable), per branch and per system"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "List of Items by Fines Stopped Reason"
- `D15` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "items that have been in-transit for more than X days (configurable)"

**Keywords:** in-transit, branches, due dates, thresholds

#### REQ-050: Circulation transaction reporting

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall count check-ins, checkouts, renewals, holds, and related transactions separately and cumulatively. Counts shall distinguish operational channels such as book drop, terminal, staff, online, OPAC, and self-service, and shall include uncataloged activity.

**Sources:**

- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "The system counts all types of check-in individually and cumulatively: - book-drop"
- `D12` Report features and interface requirements — "checkouts, check-ins, holds placed, holds filled"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "check-in counts broken down by method - book drop vs terminal vs self-service"

**Keywords:** circulation, check-ins, checkouts, renewals

### Area: collection analysis

#### REQ-005: Shelf space analysis

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall analyze collection percentages by genre and format for holdings, circulations, and shelf space. Reports shall support library and system scopes, date filtering, and shelf-space estimation from dimensions or item counts.

**Sources:**

- `D03` Shelf space vs. usage - help needed — "estimate based on item dimensions or use item count as a proxy"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "For each genre and format of material, ability to compare"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "Circulation Count by Circ Modifier (partially available)"
- `D15` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "Percentage of total circulations"

**Keywords:** shelf space, genre, format, circulation, collection

#### REQ-006: Collection comparison views

**Priority:** P3 — Could have - valuable enhancement; schedule when capacity allows.

The system shall provide side-by-side comparisons of libraries' genre and format results. Users shall also be able to compare an individual library with the system average.

**Sources:**

- `D03` Shelf space vs. usage - help needed — "a "comparison" view that shows each library's breakdown side by side"

**Keywords:** comparison, system average, libraries, formats

### Area: collection analytics

#### REQ-052: Collection metrics reporting

**Priority:** P3 — Could have - valuable enhancement; schedule when capacity allows.

The system shall report collection age and price value by call number or shelving location. Reports shall support collection evaluation and management decisions.

**Sources:**

- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "Price value of collection by call number or shelving location"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "Price value of collection by call number (not available)"

**Keywords:** collection, age, value, shelving

### Area: collection reporting

#### REQ-001: Material volume reporting

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall report material volume for a selected library and date or acquisition period. Results shall include totals, acquisitions, shelf and circulation status, category breakdowns, and changes over time.

**Sources:**

- `D01` Volume reporting - how do we count what we have? — "build reports that show volume changes over time"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "Ability to report on the volume of material in a given library at any point in time"
- `D15` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "report on volume based on acquisitions, items on shelf, and items in circulation"
- `D07` Tracking deletions - who deleted what? — "Total deletions per period (month, quarter, year)"
- `D11` Re: Financial reporting requirements - discussion thread — "value of all items with status of "longoverdue""
- `D12` Report features and interface requirements — "Activity reports showing traffic and volume of use"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "Weeding report with date of last circulation"
- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "Library Manager: Run approved reports"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "Ability to indicate last circulation date on item reports"

**Keywords:** material volume, collections, acquisitions, categories

#### REQ-002: Material status counts

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall count items associated with a selected library. Reports shall distinguish total, acquired, checked-in, checked-out, and held items, including hold counts by category.

**Sources:**

- `D01` Volume reporting - how do we count what we have? — "all three counts separately plus a total"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "generate a report of transactions (holds placed, holds filled, and check-outs) per patron, per library"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "List of Items with specific Total Use Count"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "holds placed, holds filled, and check-outs per patron, per library"

**Keywords:** item counts, status, holds, acquisitions

### Area: condition reporting

#### REQ-014: Missing damaged reporting

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall report missing and damaged items by branch. Reports shall include condition notes and support date-range filtering.

**Sources:**

- `D05` Missing and damaged items - we need a report — "The missing/damaged report can include date ranges"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "reports of missing and damaged items per branch"
- `D15` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "a report that shows all missing and damaged items per branch"
- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "Missing/damaged item reports are needed per branch"

**Keywords:** missing, damaged, conditions, branches

### Area: data access

#### REQ-045: Read-only reporting access

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The reporting system shall query OPAC and enterprise ILS data through the relational structure without modifying patron-interface data. Reporting access shall preserve the separation between management reporting and the public catalog.

**Sources:**

- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "The reporting system queries this data"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "interact with a patron interface, also known as an Online Public Access Catalog (OPAC)"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "No quick access interface with pop-up descriptions"
- `D16` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "Patrons need fast, responsive access to the catalog"
- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "Management Processes interact with a patron interface, also known as an Online Public Access Catalog (OPAC)"

**Keywords:** reporting, opac, read-only, relational

### Area: data management

#### REQ-042: Data specifications

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The developer shall provide complete data specifications and data dictionaries for authority, bibliographic, order, item, hold, request, and other records maintained or accessed by management processes. Specifications shall identify fields, data types, and relationships.

**Sources:**

- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "provide complete data specifications for authority records, bibliographic records, order records, item records, hold/request records"
- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "Other records maintained or accessed by Management Processes"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "bibliographic records, order records, item records, hold/request records"

**Keywords:** data specifications, records, fields, relationships

### Area: data quality

#### REQ-060: Data quality reporting

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall provide reports identifying incomplete or invalid catalog and patron data. Reports shall cover missing MARC fields, missing item or volume structures, invalid item types or home libraries, and excessively long call numbers.

**Sources:**

- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "Patrons with invalid home library"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "Items more than XX days overdue with patron contact info"
- `D15` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "items with long call numbers"
- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "Data quality reports are needed"

**Keywords:** data quality, catalog, marc, validation

### Area: data retention

#### REQ-055: Financial retention and privacy

**Priority:** P1 — Must have - critical for core operation, legal/audit compliance, or data integrity; blocking for the first release.

The system shall archive transaction and financial data according to applicable state and local retention requirements. Archived transaction data shall protect personally identifiable patron information while retaining useful demographic statistics and required audit history.

**Sources:**

- `D11` Re: Financial reporting requirements - discussion thread — "data archiving follows state and local requirements"
- `D12` Report features and interface requirements — "Transactions archived protecting patron privacy per State Law"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "Demographic statistics (must be anonymized - no personally identifiable info)"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "Transactions should be archived in a form that protects patron privacy as defined by State Law"
- `D17` PINES REPORTS WORKING GROUP - FIRST MEETING MINUTES — "verifying financial transactions"

**Keywords:** retention, archiving, privacy, audits

### Area: deletion auditing

#### REQ-018: Deletion audit reporting

**Priority:** P1 — Must have - critical for core operation, legal/audit compliance, or data integrity; blocking for the first release.

The system shall persist deletion events and provide queryable reports. Events shall include record type and identifier, deleting user, location, timestamp, reason when available, and denied deletion attempts; reports shall support aggregation by date, user, type, location, and system.

**Sources:**

- `D07` Tracking deletions - who deleted what? — "Fields: record_type, record_id, deleted_by, deleted_at, location"
- `D15` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "count and track record deletions per location and per system"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "Expand the available report types to cover all identified gaps"

**Keywords:** deletions, audit, compliance, records

### Area: deployment

#### REQ-038: Supported client platforms

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall be accessible through a web browser and a Windows-compatible client. It shall operate on Linux and Solaris server environments and support the explicitly requested IE 6.0-or-later and Firefox 2.0-or-later browser versions where browser access is used.

**Sources:**

- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "shall be accessible through a web-browser or a Windows-compatible client"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "accessible through a web browser or a Windows-compatible client"
- `D16` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "any reporting system needs to work on both Linux and Solaris"

**Keywords:** web browser, windows, linux, solaris

### Area: documentation

#### REQ-061: Report documentation

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The developer shall document major management processes, standard reports, bibliographic exchange, authority validation, and managed record structures. Documentation shall describe how the processes operate and interact.

**Sources:**

- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "complete data specifications for authority records"
- `D17` PINES REPORTS WORKING GROUP - FIRST MEETING MINUTES — "Document optimal Reports functionality within a future Evergreen release"
- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "and standard reports"
- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "Standard reports"

**Keywords:** documentation, processes, reports, data

### Area: environment management

#### REQ-039: Environment management

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall provide separate development, training, and production environments. Development and training activity shall not affect production data or services, and configurations shall be exportable and promotable between environments.

**Sources:**

- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "The need for separate development, training, and production environments"
- `D16` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "configurations developed in training/dev need to be migratable to production"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "ability to migrate configurations to a production environment"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "Provide a development/training environment with migration capability"

**Keywords:** development, training, production, migration

### Area: error handling

#### REQ-035: Report diagnostics

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall provide high-level reporting errors and detailed query-specific diagnostics to authorized administrators. Diagnostics shall identify relevant tables, fields, and error types when available.

**Sources:**

- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "allow low-level query-specific feedback for Local and Global System Administrators from the front-end interface"
- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "which table, which field, what kind of error"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "provide thorough high-level error reporting and feedback"

**Keywords:** errors, diagnostics, queries, fields

### Area: financial reporting

#### REQ-053: Financial reporting

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall report patron balances, fines, charges, waived fines, payments, bills, and aged debt. Reports shall support time-period, branch, payment-method, charge-type, patron, home-library, and system dimensions.

**Sources:**

- `D11` Re: Financial reporting requirements - discussion thread — "Fines waived per time period and per branch"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "fines waived per time period and per branch"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "Aged Debt detailed report (partially available, needs enhancement)"

**Keywords:** financial, fines, payments, balances, debt

### Area: financial services

#### REQ-054: Payment traceability

**Priority:** P1 — Must have - critical for core operation, legal/audit compliance, or data integrity; blocking for the first release.

The system shall associate fines, charges, waivers, and electronic transactions with patron and item records. It shall maintain a payment ledger tracing each payment to the charge or charges to which it was applied.

**Sources:**

- `D11` Re: Financial reporting requirements - discussion thread — "Fines, charges, waivers, and ecommerce transactions are attached to patron and item records."
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "Fines, charges, waivers, and ecommerce transactions are attached to patron and item records"

**Keywords:** payments, ledger, charges, traceability

### Area: general

#### REQ-063: Report the number of board books

**Priority:** P3 — Could have - valuable enhancement; schedule when capacity allows.

The system shall report the number of board books. This capability is required by the source corpus.

**Sources:**

- `D01` Volume reporting - how do we count what we have? — "Number of board books"

**Keywords:** board, book, number, report

#### REQ-064: Allow transactions to be queried either collectively or by transaction

**Priority:** P3 — Could have - valuable enhancement; schedule when capacity allows.

The system shall allow transactions to be queried either collectively or by transaction type. This capability is required by the source corpus.

**Sources:**

- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "can be queried by all transactions or by type of transaction"

**Keywords:** collectively, either, queried, transaction, type

#### REQ-065: Provide a list of patrons who are barred

**Priority:** P3 — Could have - valuable enhancement; schedule when capacity allows.

The system shall provide a list of patrons who are barred. This capability is required by the source corpus.

**Sources:**

- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "List of patrons who are BARRED"

**Keywords:** barred, list, patron, who

#### REQ-066: Provide a report of IntraPINES loans by facility

**Priority:** P3 — Could have - valuable enhancement; schedule when capacity allows.

The system shall provide a report of IntraPINES loans by facility. The system shall provide a report of IntraPINES loans by system. The system shall provide a report of IntraPINES loans for all facilities.

**Sources:**

- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "IntraPINES Loans for all Facilities"

**Keywords:** facility, intrapine, loan, report

#### REQ-067: Provide monthly counts of noncataloged in-house use

**Priority:** P3 — Could have - valuable enhancement; schedule when capacity allows.

The system shall provide monthly counts of noncataloged in-house use. This capability is required by the source corpus.

**Sources:**

- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "NonCat In House Use Count by Month"

**Keywords:** count, house, monthly, noncataloged

#### REQ-068: Show when a report was submitted

**Priority:** P3 — Could have - valuable enhancement; schedule when capacity allows.

The system shall show when a report was submitted. This capability is required by the source corpus.

**Sources:**

- `D12` Report features and interface requirements — "When their report was submitted"

**Keywords:** report, show, submitted

#### REQ-069: Provide hover tooltips for report titles

**Priority:** P3 — Could have - valuable enhancement; schedule when capacity allows.

The system shall provide hover tooltips for report titles. This capability is required by the source corpus.

**Sources:**

- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "No hover tooltips for report titles"

**Keywords:** hover, report, title, tooltip

#### REQ-070: Group transactions by hour

**Priority:** P3 — Could have - valuable enhancement; schedule when capacity allows.

The system shall group transactions by hour. This capability is required by the source corpus.

**Sources:**

- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "Transactions can be grouped by hour"

**Keywords:** group, hour, transaction

#### REQ-071: Support program attendance tracking reports

**Priority:** P3 — Could have - valuable enhancement; schedule when capacity allows.

The system shall support program attendance tracking reports. This capability is required by the source corpus.

**Sources:**

- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "Program attendance tracking"

**Keywords:** attendance, program, report, tracking

### Area: help

#### REQ-058: Online help

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall provide comprehensive online help in HTML describing and illustrating system functions. Help shall be hierarchical, searchable, cross-linked, and usable with screen readers.

**Sources:**

- `D16` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "online, hierarchical, and cross-linked"
- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "provide an online, hierarchical, and cross-linked help system in HTML"
- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "The system shall provide an online, hierarchical, and cross-linked help system in HTML"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "online, hierarchical, and cross-linked help system in HTML"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "No online help system integrated with reports"

**Keywords:** online help, html, searchable, screen readers

### Area: historical reporting

#### REQ-040: Historical reporting

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall support real-time operational reporting and historical reports for specified dates or date ranges. A reporting warehouse or equivalent retained store shall preserve prior values, including shelving locations, bills, transaction aggregates, and other values needed for point-in-time snapshots.

**Sources:**

- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "Some reports need to be real-time"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "Need a snapshot bills report going back in time"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "historical reporting - a reporting warehouse such that data can be acquired on a given date or date range"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "Snapshot bills report going back in time"

**Keywords:** historical, snapshots, warehouse, retention

### Area: inactive patrons

#### REQ-021: Inactive patron reporting

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall identify patrons with no circulation or electronic activity during a configurable period. Results shall include current mailing addresses and support grouping by system, home library, and county.

**Sources:**

- `D09` Inactive patrons report needed — "no circulation or electronic"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "patrons with no circulation or electronic activity in the last X days (X configurable)"
- `D17` PINES REPORTS WORKING GROUP - FIRST MEETING MINUTES — "This does NOT include day-to-day patron-facing functions"

**Keywords:** inactive patrons, activity, addresses, organizations

#### REQ-022: Inactive patron exclusions

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The inactive-patron report shall allow users to configure exclusions. Exclusions shall support do-not-disturb patrons, communication opt-outs, staff members, and VIP patrons.

**Sources:**

- `D09` Inactive patrons report needed — "Patrons who have opted out of communications"

**Keywords:** inactive patrons, exclusions, staff, opt-outs

#### REQ-023: Inactive patron processing

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall allow the inactivity period to be configured in days and shall process long-running inactive-patron reports in the background. Results shall be cacheable and exportable to CSV, with patrons owing fines separately identified.

**Sources:**

- `D09` Inactive patrons report needed — "run it as a background report"
- `D16` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "we need to make sure reports can be queued and processed in the background"
- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "We need background processing/queuing"

**Keywords:** inactive patrons, background reports, csv, fines

#### REQ-024: Electronic activity definition

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

For inactivity analysis, the system shall count recorded access to integrated digital collections, OPAC or account logins, online hold placement, and online renewals as electronic activity.

**Sources:**

- `D09` Inactive patrons report needed — "Accessing digital collections (if integrated)"

**Keywords:** electronic activity, opac, digital collections, renewals

### Area: item maintenance

#### REQ-048: Item status conversion

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall identify items for status conversion and support batch changes from one status to another. Reports and utilities shall assist staff with large conversions such as missing to discard/weed.

**Sources:**

- `D06` Weeding reports - item purging needs — "changing 100 items from "missing" to "discard/weed" at once"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "a report to assist in the conversion of items from one status to another"
- `D15` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "change 100 items from "missing" to "discard/weed" in batch"

**Keywords:** item status, batch, conversion, missing

### Area: item transfers

#### REQ-007: Transfer candidate selection

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall query candidate materials for transfer and allow users to select individual titles or items from the results. Users shall be able to save and reuse transfer queries, subject to authorization when sharing them.

**Sources:**

- `D04` Moving items between branches - utility needed — "Manually select titles from query results"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "Ability to manually select titles from query results"
- `D15` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "manually select titles from query results"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "Query for candidate materials"

**Keywords:** transfers, queries, selection, saved queries

#### REQ-008: Transfer location updates

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

Authorized users shall be able to transfer selected items between branches or temporary program locations. The system shall update each selected item record with its new location.

**Sources:**

- `D04` Moving items between branches - utility needed — "Change records of selected items to new location"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "Ability to change records of selected items to move to new location"
- `D15` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "change records of selected items to move them to a new location"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "Change records to move items to new location"

**Keywords:** transfers, locations, items, branches

#### REQ-009: Transfer preview confirmation

**Priority:** P1 — Must have - critical for core operation, legal/audit compliance, or data integrity; blocking for the first release.

The system shall show the items and locations affected by a proposed transfer before applying changes. It shall require explicit confirmation before committing the transfer.

**Sources:**

- `D04` Moving items between branches - utility needed — "the utility should show a preview before making changes"

**Keywords:** transfer preview, confirmation, affected items, locations

#### REQ-010: Batch transfer processing

**Priority:** P1 — Must have - critical for core operation, legal/audit compliance, or data integrity; blocking for the first release.

The system shall process batches of item transfers safely and efficiently. Large operations shall use transaction-safe processing and smaller batches when needed to avoid database locking.

**Sources:**

- `D04` Moving items between branches - utility needed — "process in smaller batches to avoid locking the database"

**Keywords:** batch transfers, transactions, locking, branches

#### REQ-011: Transfer logistics outputs

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall generate pull lists and printable transit labels for transferred items. Transit labels shall contain identifying barcode information.

**Sources:**

- `D04` Moving items between branches - utility needed — "generate transit labels"
- `D06` Weeding reports - item purging needs — "That haven't circulated in 5+ years"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "generating pull lists"
- `D15` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "merge the transit-to and transit-from into one report"

**Keywords:** pull lists, transit labels, barcodes, transfers

#### REQ-012: Transfer history and reversion

**Priority:** P1 — Must have - critical for core operation, legal/audit compliance, or data integrity; blocking for the first release.

The system shall retain transfer history for audit and support undo or automatic restoration of transferred items. Reversion shall be configurable by elapsed time, status, checkout, or event completion.

**Sources:**

- `D04` Moving items between branches - utility needed — "revert "based on other criteria""
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "Transaction history is maintained for X days (X is configurable)"
- `D15` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "reverting items back to their original location after a set period of time"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "Transaction history maintained for X days (configurable)"

**Keywords:** transfer history, reversion, undo, audit

### Area: management reporting

#### REQ-056: Management analytics

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall provide analysis for branch capacity, collection distribution and use, patron demographics and interests, staff productivity, and workflows. Results shall support planning, evaluation, and oversight.

**Sources:**

- `D17` PINES REPORTS WORKING GROUP - FIRST MEETING MINUTES — "reports and analysis tools used by library managers, administrators, and staff for planning, evaluation, and oversight purposes"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "Analyzing branch capacity and optimal distribution of the collection."
- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "Demographic analysis for program planning"

**Keywords:** management, analytics, collections, productivity

### Area: patron reporting

#### REQ-019: Patron demographic reporting

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall allow patron reports to filter and group by configurable demographic, geographic, organizational, language, ZIP code, patron type, and survey characteristics. Reports shall support both filtering and aggregate grouping.

**Sources:**

- `D08` Patron reports by demographics - how? — "Both LIMIT (filter) and GROUP BY (aggregate) should be supported"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "Patron Count by County, City, and Zip Code"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "Patron Count by County, City, & Zip Code"

**Keywords:** patrons, demographics, grouping, geography

#### REQ-020: Patron age calculation

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall calculate patron age ranges from birth dates when reports execute. Patrons missing optional characteristics shall remain in results with null values.

**Sources:**

- `D08` Patron reports by demographics - how? — "We should include them in the report (with null values)"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "List of Patrons by Expiration Date"
- `D12` Report features and interface requirements — "Cross- tabulated per terminal, per branch, per system, per hour, per age range,"

**Keywords:** patron age, birth date, null values, reports

### Area: performance

#### REQ-041: Reporting performance isolation

**Priority:** P1 — Must have - critical for core operation, legal/audit compliance, or data integrity; blocking for the first release.

Searches and reports shall run during open hours without materially disrupting operational services or slowing the OPAC. The system shall use background processing, a reporting database, a replica, or an equivalent isolation mechanism.

**Sources:**

- `D16` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "searches and reports can be processed during open hours without disrupting other system functions"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "No separate reporting database/replica"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "searches and reports can be processed during open hours without disrupting other system functions"
- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "requires the system to check for cancellation signals during report processing"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "Reports take too long to run during busy hours"

**Keywords:** performance, opac, replica, reporting

### Area: querying

#### REQ-025: Query construction

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall provide a user-friendly query builder across supported record types. Users shall be able to select fields and values, use picklists and regular expressions, and combine criteria with Boolean operators.

**Sources:**

- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "against all record types (bibliographic, item, patron, transaction, financial)"
- `D12` Report features and interface requirements — "Staff should be able to select fields to query"

**Keywords:** queries, boolean, picklists, fields

### Area: record maintenance

#### REQ-049: Empty record deletion

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall efficiently delete bibliographic records with no attached items. It shall also support deleting volume entries together with associated copy entries.

**Sources:**

- `D06` Weeding reports - item purging needs — "deleting volume entries along with copy entries"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "deleting volume entries along with copy entries"
- `D15` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "deleting volume entries along with copy entries"

**Keywords:** deletion, bibliographic, volumes, copies

### Area: record purging

#### REQ-015: Purge candidate criteria

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall allow authorized users to define and combine purge criteria. Criteria shall include item status, time in status, last circulation, and conditions such as missing, damaged, or discard/weed.

**Sources:**

- `D06` Weeding reports - item purging needs — "Status-based criteria (missing, discard/weed, damaged)"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "An item has status "discard/weed""
- `D15` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "Item has status "discard/weed""

**Keywords:** purging, criteria, status, circulation

#### REQ-016: Purge review and last copies

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall provide read-only reports and utilities for reviewing purge candidates before deletion. It shall identify whether an item is the last copy within a selected library, system, or consortium scope.

**Sources:**

- `D06` Weeding reports - item purging needs — "Reports show candidates for purging (read-only)"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "provide a last copy report that singles out a library system's last copies"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "Last Copy Report (partially available, needs enhancement)"
- `D15` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "This singles out a library system's last copies"

**Keywords:** purging, last copy, review, reports

#### REQ-017: Controlled purge execution

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall require separate confirmation before executing purge deletions. It shall record who performed each purge and when, and shall support scheduled purge execution.

**Sources:**

- `D06` Weeding reports - item purging needs — "A separate confirmation step for actual deletions"
- `D07` Tracking deletions - who deleted what? — "Who deleted it"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "Count and track record deletions"

**Keywords:** purging, confirmation, audit, scheduling

### Area: report authoring

#### REQ-028: Report authoring

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

Authorized users shall be able to create, clone, modify, and run report templates, including canned, on-demand, and open-template reports. Administrators shall be able to provide shared folders and predefined templates while restricting unsafe or unauthorized modifications.

**Sources:**

- `D12` Report features and interface requirements — "Admins can create shared folders"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "Three interfaces (canned, on-demand, open template)"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "System administrators should be able to create shared folders"
- `D13` Staff login difficulties - need for streamlined access — "Department heads (can create and modify templates)"
- `D17` PINES REPORTS WORKING GROUP - FIRST MEETING MINUTES — "Determine and create templates needed for all PINES libraries"
- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "Determine and create templates needed for all PINES libraries"
- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "limited template modification"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "Shared folders to allow/disallow staff from running specific reports."

**Keywords:** reports, templates, authoring, canned reports

### Area: report distribution

#### REQ-034: Report scheduling and delivery

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

Users shall be able to run reports immediately or schedule hourly, daily, weekly, monthly, or yearly execution. Scheduled results shall support configurable email recipients and recipient address books.

**Sources:**

- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "No address book for report delivery"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "Ability to select Run ASAP, Hourly, Daily, Weekly, Monthly, Yearly"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "Email delivery of reports"

**Keywords:** reports, scheduling, email, recipients

### Area: report filtering

#### REQ-030: Report filtering

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

Users shall be able to filter reports using available fields and uploaded values. Text files containing barcodes or TCNs shall be usable as filter inputs, and survey names shall resolve to their internal identifiers.

**Sources:**

- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "No ability to upload text files for filtering"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "upload a text file such as barcodes or TCN to use for filtering on a report"
- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "requires the system to resolve names to IDs internally"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "Can't filter by some fields that should be available"

**Keywords:** reports, filters, barcodes, tcns, surveys

### Area: report output

#### REQ-031: Report output formats

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall export report results in CSV, Excel, and HTML formats. HTML shall be standards-compliant, and exports shall preserve record structure without introducing duplicate rows.

**Sources:**

- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "Output would be in Excel, HTML, and CSV format"
- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "Excel, HTML, and CSV formats are required"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "export to Excel but the data has too many duplicate rows"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "Provide multiple output formats and scheduling options"

**Keywords:** csv, excel, html, exports

### Area: report processing

#### REQ-033: Report execution queue

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall execute long-running reports as background jobs in a managed queue. Users shall see queue position, submission time, status, completion or failure, and shall be able to cancel scheduled or running reports and prioritize important report types.

**Sources:**

- `D12` Report features and interface requirements — "A director's board report should be able to jump ahead of a staff member's ad-hoc query."
- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "cancel a scheduled or running report"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "No background processing for long-running reports"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "Staff should be able to see where their report is in the queue"
- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "Report queue visibility is important"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "Ability to see where your report is in the queue."

**Keywords:** reports, queue, background, cancellation, status

### Area: report results

#### REQ-032: Report result context

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

Report results shall include the query selections, date criteria, null values, and blank fields used or returned by the report. This context shall allow users to interpret and reproduce the result set.

**Sources:**

- `D12` Report features and interface requirements — "System provides query selections along with results."
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "All nulls and blank fields must be included in the results"
- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "All nulls and blank fields must be included in the results"
- `D14` EVERGREEN ILS - REPORTING MODULE OVERVIEW — "All nulls and blank fields included in results"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "All nulls and blank fields must be included in results"

**Keywords:** reports, criteria, nulls, traceability

### Area: report security

#### REQ-029: Report safeguards

**Priority:** P1 — Must have - critical for core operation, legal/audit compliance, or data integrity; blocking for the first release.

Report template changes shall not compromise result accuracy or expose excluded records. The system shall prevent unauthorized changes that would display deleted items or alter protected selection and display rules.

**Sources:**

- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "they should not be able to alter the template to display deleted items"
- `D12` Report features and interface requirements — "can't alter the template to display deleted items."
- `D11` Re: Financial reporting requirements - discussion thread — "System can generate a report of the value of items (based on data in item record)"

**Keywords:** reports, accuracy, safeguards, deleted records

### Area: reporting

#### REQ-059: Staff and operational reports

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall provide predefined operational, analytical, financial, board, executive, inventory, capacity, demographic, transit, shelf-space, weeding, and staff productivity reports. Reports shall support consortium-wide and participating-library scopes.

**Sources:**

- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "Board/executive reports need to be pre-defined"
- `D20` PINES STAFF REPORTS SURVEY - RESULTS SUMMARY — "Staff productivity reports (time spent per transaction)"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "basic statistics like those required by the Georgia Annual Report and Application for State Aid"
- `D12` Report features and interface requirements — "Pre-defined reports for library boards"

**Keywords:** reports, executive, inventory, operations, staff

### Area: system integration

#### REQ-044: Enterprise ILS integration

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

Management processes shall operate with the enterprise ILS data structures and Acquisitions and Cataloging functionality. The system shall support multiple library locations, interact with the OPAC without constraining it, and exchange vendor data through APIs and standard files.

**Sources:**

- `D18` PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES — "rely on the data structures and functionality of an enterprise-level Library Automation System, including Acquisitions and Cataloging modules"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "rely on the data structures and functionality of an enterprise-level Library Automation System"
- `D19` PINES TECHNICAL SUBCOMMITTEE MEETING NOTES — "Management Processes rely on the data structures and functionality of an enterprise-level Library Automation System"

**Keywords:** ils, opac, vendors, integration

### Area: uncataloged materials

#### REQ-046: Uncataloged inventory tracking

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall track uncataloged materials as inventory even without complete catalog records. Inventory records shall support counting, circulation reporting, and identification of how materials are used.

**Sources:**

- `D15` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "track these as inventory even though they're not fully cataloged"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "Ability to control inventory of uncataloged material"
- `D17` PINES REPORTS WORKING GROUP - FIRST MEETING MINUTES — "Tracking and verifying financial transactions"

**Keywords:** uncataloged, inventory, circulation, tracking

#### REQ-047: Uncataloged material processing

**Priority:** P2 — Should have - important for the daily workflows of key stakeholders; implement in the first release if feasible.

The system shall support rapid distribution and processing of uncataloged materials while minimizing branch labor. Workflows shall support high-volume handling and quick distribution.

**Sources:**

- `D15` PINES REPORTS WORKING GROUP - INTERVIEW RECORD — "quick distribution (we need to process these fast)"
- `D10` DRAFT SOFTWARE REQUIREMENTS SPECIFICATION — "Minimal branch labor"

**Keywords:** uncataloged, processing, distribution, labor

## 5. Blacklist (discarded candidates)

Candidates that were identified but deliberately discarded, with the reason for each rejection:

| ID | Candidate | Category | Reason | Source |
|---|---|---|---|---|
| BL-001 | Project shall develop a list of reports requirements | nonsensical | The quoted candidate is a project/management task ("develop a list of requirements") rather than a system functional or non-functional requirement. It does not describe system behaviour or capabilities to be delivered by the software and therefore is not an appropriate item for the requirements set. | D18 |

## 6. Coverage appendix (document → requirements)

| Doc | Document | Candidates | Requirements citing it | Blacklist entries |
|---|---|---|---|---|
| D01 | Volume reporting - how do we count what we have? (conversations/conv_pines014_material_volume.eml) | 18 | 3 | 0 |
| D02 | Can we see all branches at once? (conversations/conv_pines015_capacity_interface.eml) | 9 | 2 | 0 |
| D03 | Shelf space vs. usage - help needed (conversations/conv_pines016_shelf_space.eml) | 11 | 2 | 0 |
| D04 | Moving items between branches - utility needed (conversations/conv_pines018_item_transfer.eml) | 26 | 7 | 0 |
| D05 | Missing and damaged items - we need a report (conversations/conv_pines019_020_missing_intransit.eml) | 9 | 2 | 0 |
| D06 | Weeding reports - item purging needs (conversations/conv_pines021_item_purging.eml) | 21 | 6 | 0 |
| D07 | Tracking deletions - who deleted what? (conversations/conv_pines022_deletions.eml) | 20 | 3 | 0 |
| D08 | Patron reports by demographics - how? (conversations/conv_pines023_patron_characteristics.eml) | 14 | 2 | 0 |
| D09 | Inactive patrons report needed (conversations/conv_pines024_inactive_patrons.eml) | 20 | 4 | 0 |
| D10 | DRAFT SOFTWARE REQUIREMENTS SPECIFICATION (early_draft_srs_galecia.txt) | 270 | 57 | 0 |
| D11 | Re: Financial reporting requirements - discussion thread (email_financial_reports.eml) | 24 | 5 | 0 |
| D12 | Report features and interface requirements (email_report_features.eml) | 36 | 12 | 0 |
| D13 | Staff login difficulties - need for streamlined access (email_staff_login.eml) | 13 | 3 | 0 |
| D14 | EVERGREEN ILS - REPORTING MODULE OVERVIEW (evergreen_reference_2009.txt) | 64 | 24 | 0 |
| D15 | PINES REPORTS WORKING GROUP - INTERVIEW RECORD (interview_cataloging_2009-05-08.txt) | 37 | 16 | 0 |
| D16 | PINES REPORTS WORKING GROUP - INTERVIEW RECORD (interview_sysadmin_2009-05-10.txt) | 40 | 11 | 0 |
| D17 | PINES REPORTS WORKING GROUP - FIRST MEETING MINUTES (meeting_minutes/meeting_2009-03-15_minutes.txt) | 16 | 7 | 0 |
| D18 | PINES REPORTS WORKING GROUP - SECOND MEETING MINUTES (meeting_minutes/meeting_2009-07-20_minutes.txt) | 52 | 19 | 1 |
| D19 | PINES TECHNICAL SUBCOMMITTEE MEETING NOTES (meeting_tech_subcommittee_2009-06-30.txt) | 54 | 18 | 0 |
| D20 | PINES STAFF REPORTS SURVEY - RESULTS SUMMARY (survey_results_2009.txt) | 66 | 21 | 0 |

## 7. Review log

| Iteration | Passed | Issues | Kinds | Notes |
|---|---|---|---|---|
| 1 | no | 7 | conflict, duplicate, priority | The requirements have real duplication and compatibility conflicts that need resolution. All candidate-producing documents are cited by at least one requirement; the supplied data does not establish any unreasoned discarded candidates. |
| 2 | no | 12 | blacklist, coverage, duplicate, trace | The specification has significant duplicate requirements and one suspicious source trace. All candidate-producing documents are represented, but browser-version scope and the legacy-browser blacklist need clarification. |
| 3 | no | 5 | conflict, coverage, duplicate | The specification has unresolved candidate coverage, substantial over-merging, accessibility duplication/overlap, and a compatibility conflict. Requirement IDs, priorities, and blacklist rationale show no clear defects. |

*Final QA verdict:* no (iteration budget exhausted - see review log)

*Post-review deterministic audit:* 0 uncovered candidate refs, 1 blacklist entries; 26 advisory coverage issue(s).
