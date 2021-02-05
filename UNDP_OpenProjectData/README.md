# OPEN.UNDP.ORG

[open.undp.org](http://open.undp.org), which presents detailed information on the UNDP’s 5,000+ development projects in some 170 countries and territories worldwide. Browse the summaries, click a filter on the right, or search through the full list of projects. It represents UNDP’s commitment to publish comprehensive, quality and timely information about aid flows and results. 

Open.undp.org enables users to find project information categorized broadly by location, funding source, and focus areas, and drill down for comprehensive project data, including budget, expenditure, completion status, implementing organization, contribution to gender equality, project documents, and more. Open.undp.org features current project site images and is integrated with UNDP country office external web sites to enhance knowledge sharing.

## API Documentation 
Brief description of API is available under Download menu, open in a pop-up window.
```
JSON
Individual Project Data: https://api.open.undp.org/api/projects/{project - id}.json
Project Summaries: https://api.open.undp.org/api/project_summary_{year}.json
Operating Unit Data: https://api.open.undp.org/api/units/{operating - unit}.json
Operating Unit Index: https://api.open.undp.org/api/units/operating-unit-index.json
Sublocation Location Index: https://api.open.undp.org/api/sub-location-index.json
Region Index: https://api.open.undp.org/api/region-index.json
Donor Index: https://api.open.undp.org/api/donor-index.json
Donor by Country Index: https://api.open.undp.org/api/donor-country-index.json
Focus Area Index: https://api.open.undp.org/api/focus-area-index.json
Aid Classification Index: https://api.open.undp.org/api/crs-index.json
SDG Index: https://api.open.undp.org/api/sdg-index.json
Individual Output Data: https://api.open.undp.org/api/outputs/{output - id}.json
SDG Target index: https://api.open.undp.org/api/target-index.json
Individual SDG Target index: https://api.open.undp.org/api/target-index/{sdg - id}.json
Signature solution index: https://api.open.undp.org/api/signature-solutions-index.json
Our Approaches index: https://api.open.undp.org/api/our-approaches-index.json
Project Data: https://api.open.undp.org/api/project_list/?year={year}&sector={sector-id}&operating_unit={iso3}&sdg={sdg-id}&signature_solution={signature solution-id}&budget_source={budget source-id}&marker_type={marker-id}&limit={1-1000}&offset={0-count/1000}

Comma Separated Values
[undp-project-data.zip](https://api.open.undp.org/api/download/undp-project-data.zip)
```

## Particularities 
**Scope of project data varies**. Finanacial data and main information is available for all projects. Additional information--SDG markers, results, project documents--is typically not available for older projects. Check project data keys to access data. For instance, to print SDGs related to the projects: 
```
if "sdg" in p_data.keys():
    print(f"    SDGs: {', '.join([s['id'] for s in p_data['sdg']])}")
```

## Code Examples
**Access UNDP Project Data and Files.py** Python script for downloading all project data for all operational units
**Access UNDP Project Results.py** Python script for getting project results. Note that project results are available for a limited number of projects. 

## Legal considerations
The data used on the [open.undp.org](http://open.undp.org) is free to use under the Creative Commons Attribution 3.0 IGO License (CC-BY 3.0 IGO).


