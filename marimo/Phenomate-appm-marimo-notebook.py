# /// script
# dependencies = [
#   "appm",
#   "marimo>=0.25.0",
#   "tzdata",
# ]
# ///

import marimo

__generated_with = "0.25.0"
app = marimo.App(
    width="full",
    app_title="Test for appn-project-manager library",
)


@app.cell(hide_code=True)
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## APPM Template File Demo
    This worksheet lets us test the effect of changing the `appn-project-manager` library template file used (`/tmp/template.yaml`) and view the output directory that is created using the initialised library and a specific filename structure.
    
    ### To use this worksheet
    Click the `play` button ▶ in the bottom right corner to run all the cells. If you modify a cell, then re-run the cell using the cell play button. The other dependent cells should re-run, however sometimes they will not if a dependency is a file that is saved and not a Python variable, so manually re-run the cells that follow.
    
    There is a [Wiki site](https://github.com/aus-plant-phenomics-network/appn-project-manager/wiki) that tries to explain the use of the appm library, however it is thought that interactive use of the library is a more practical way for getting to understand what parameters control the final output structure.

    ---
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion( {"Requirements": mo.md(r"""

    ## Requirements

    ### Use the Github.io hosted version
    This workbook is available here [https://aus-plant-phenomics-network.github.io/appn-project-manager/](https://aus-plant-phenomics-network.github.io/appn-project-manager/) and is run directly in you browser.

    ### Local hosting of the workbook
    To run this workbook, we need the library `marimo` installed which allows us to run an interactive Python notebook.

    #### Install marimo
    Install marimo into a virtual environment using the `uv` package manager
      ```bash
      # If required install uv: curl -LsSf https://astral.sh/uv/install.sh | sh
      # Create and move into a working directory
      mkdir appm-test; cd appm-test
      # create uv virtual environment
      uv venv
      # load venv
      source .venv/bin/activate
      # install marimo
      uv pip install marimo
      ```

    #### Install appn-project-manager
    appn-project-manager library can be installed as a package or from the Github repository.

    - The `appm` library can be installed using `uv`:
      ```bash
      uv pip install appm
      ```

    - Or, install `appm` from Github:
      ```bash
      git clone https://github.com/aus-plant-phenomics-network/appn-project-manager.git
      # if not done, also install marimo
      # uv pip install marimo
      # N.B. set the variable path_to_repo in the cell below.
      ```

    #### Run the marimo workbook

      ```bash
      marimo edit Phenomate-appm-marimo-notebook.py
      ```

    ### Repository
      appn-project-manaer repository site: [github.com/aus-plant-phenomics-network/appn-project-manager](https://github.com/aus-plant-phenomics-network/appn-project-manager)
    ---
    """
    )})
    return


@app.cell(hide_code=True)
def _(mo):

    mo.accordion( {"APPN Metadata and Project Structure Discussion": mo.md(r"""
    ### APPN Field Site data/metadata standards
    The APPN nodes have a defined output directory structure for the UAV data. This directory structure is to be followed for the Phenomate data collection activities.

    Some details are availabe here: [APPN-Field-Protocols-and-Pipelines/wiki/Data-Folder-Structure](https://github.com/aus-plant-phenomics-network/APPN-Field-Protocols-and-Pipelines/wiki/Data-Folder-Structure)

    To reiterate the above the standard output directory is:

    ```bash
    ./{NodeName}/{Project}/{Site}/{Sensor}/{YYYYMMDD}/Run_{XX}/T0_raw
    ```

    The above recommended structure lacks a timezone specification in the date section, which can end in a mismatch of dates if timestamps that are embedded in a filename are collect in UTC and not converted to local time. The `date_convert` part of the `layout` section of the template.yaml file (see below) can be choosen to format the output directory with or without a timezone section and can help with conversion of date strings between timezones.

    > The example template.yaml file in this worksheet has been developed to follow the APPN standard directory structure for data layout.
    > The directory structure is just one part of the standards defined for APPN project data outputs. See the above *APPN-Field-Protocols* site for discussion of other standards, such as the need for definition of [plot layout files and metadata](https://github.com/aus-plant-phenomics-network/APPN-Field-Protocols-and-Pipelines/wiki/Plot-Delineation#appn-plot-shapefile-standard).

    ### APPN Booking metadata
    There is also a schema definition that can be used for project ***booking*** metadata that can be used to get the essential information needed to describe a project and have it collated as a project progresses. This schema is currently available here: [docs/er_diagram/er_diagram_from_tab_to_schema/jsonschema_current](https://github.com/aus-plant-phenomics-network/appn-schema/tree/main/docs/er_diagram/er_diagram_from_tab_to_schema/jsonschema_current)

    ---
    """)})
    return


@app.cell(hide_code=True)
def _():
    import os

    try:
        # if installed using uv/pip
        import appm
    except ImportError:
        # we now assume that the git repo has been installed - set the path here
        home_str = os.getenv("HOME")
        path_to_repo = home_str + '/APPN/repos/appn-project-manager'  
        os.chdir(path_to_repo)

    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### The template.yaml file
    The following cells allow the interactive use of the `appm` library to see how it uses project data and filename information to create a output directory structure, ready for file transfer from the set of Phenomateinstruments.

    Use the following file writer cell to modify the input `template.yaml` file that is used in the ProjectManager initialisation below:
    """)
    return


@app.cell
def _():
    # This is an example template.yaml file. Modify it to see how it affects the output data structure
    # using the code cells below.
    template_file = """
    version: 0.1.2

    # The naming_convention section describes the base directory where the project data will reside.
    # The variables available are any used in the ProjectManager.from_template() method (see example below)
    naming_convention:
      # Use `sep: "/"` to specify elements as separate 
      #   directories : <root>/organisationName/project/site/platform
      # or any other string e.g. `sep: "_"` to concatenate all elements into 
      #   a single directory name : <root>/organisationName_project_site_platform
      sep: "/"
      # The following list variables in the following order are used in construction of a base directory:
      structure: ['organisationName', 'project', 'site', 'platform']


    # The layout section describes the directory where the data will be placed, and the variables available
    # are those derived from the filename:
    layout:
      structure: [  'date', 'site_fn', 'procLevel', 'sensor' ]
      mapping:
        procLevel:
          raw: 'T0-raw'
          proc: 'T1-proc'
          trait: 'T2-trait'
      date_convert:
        base_timezone: 'UTC'                   # This is the default tz if none is found in the filename
        output_timezone: 'Australia/Adelaide'  # This is the output tz after interpreting the base tz
        input_format: '%Y-%m-%d %H-%M-%S'      # concatenated (with a space) filename components: 'date' and 'time' 
        output_format: '%Y%m%d%z'              # this is how the directory will be formatted

    # The file section describes the structure of the input filenames and
    # has sections to describe files with differing extensions (e.g. below are for .bin and .csv)
    file:
      "bin":
        sep: "_"
        # preprocess section allows basic find and replace of characters within a filename
        # which can be a 'quick fix' for deviations in the filename structure used by the 
        # Amiga collection system
        # The example below replaces '-' with '_' but only if the '-' is followed by one 
        # of the following strings: jai|imu|Lidar|Hyperspec
        preprocess:
          find: '-(?=(jai|imu|Lidar|Hyperspec|Ouster))'
          replace: '_'
          casesensitive: 'False'
        default:
          procLevel: raw
        components:
          - sep: "_"
            components:   # N.B. the format of the data and time string need to match what's used in 'layout' 'date_convert' above
              - ['date', '\d{4}-\d{2}-\d{2}']
              - ['time', '\d{2}-\d{2}-\d{2}']
          - ['ms', '\d{6}']      
          - name: 'timezone'
            pattern: '[+-]\d{4}'
            required: false
          - ['site_fn', '[^_.]+']
          - ['sensor', '[^_.]+']
          - name: 'procLevel'
            pattern: 'T0-raw|T1-proc|T2-trait|raw|proc|trait'
            required: false
      "csv":
        sep: "_"
        preprocess:
          find: '-(?=(canbus))'
          replace: '_'
          casesensitive: 'False'
        default:
          procLevel: raw
        components:
          - sep: "_"
            components:
              - ['date', '\d{4}-\d{2}-\d{2}']
              - ['time', '\d{2}-\d{2}-\d{2}']
          - ['ms', '\d{6}']
          - name: 'timezone'
            pattern: '[+-]\d{4}'
            required: false
          - ['sensor', '[^_.]+']
          - ['site_fn', '[^_.]+']      
          - name: 'procLevel'
            pattern: 'T0-raw|T1-proc|T2-trait|raw|proc|trait'
            required: false 
    """
    # Save the above yaml text to a file to be read by the subsequent method
    from pathlib import Path
    Path("/tmp/template_config.yaml").write_text(template_file, encoding="utf-8")
    return


@app.cell
def _(mo):
    from appm import ProjectManager

    # The information specified here is combined with the filename information to determine an output directory name.
    # All of these method parameters are available for use in the template.yaml file 'naming_convention` `structure` list.
    pm = ProjectManager.from_template(
        root="/mnt/research_data/data/phenomate",  # say this is a mount point on a network directory i.e. STAAS
        year=2025,
        summary="summary-001",
        platform="phenomate",
        project="OzBarley_01",
        site='Horsham',
        internal=True,
        researcherName=None,
        organisationName="Adelaide-University",   # the APPN node name
        template="/tmp/template_config.yaml"      # The template file. In this demo case, it is defined in the cell above.
    )

    # pm.location is the the base directory structure as a PosixPath
    mo.md(f"Defined project base directory (pm.location): `{pm.location}`")

    # The pm.init_project() method would create the base directory structure 
    # at pm.location 
    # pm.init_project() 
    return (pm,)


@app.cell
def _(mo, pm):
    # Filename parts - format should match what is in 'components' regex section of template.yaml
    date_str = "2025-08-15"
    time_str = "06-30-03"
    ms_str = "395000"
    timezone_str = "+0930"  # this is not required if the filename. UTC is then assumed
    site_fn_str ="run-001"
    sensor_str = "jai1"
    extension_str = ".bin"

    filename_list = [date_str, time_str, ms_str, timezone_str, site_fn_str, sensor_str]
    # concatenate the filename components 
    filename_joined = "_".join(filename_list)+ extension_str


    _mo0 = mo.md(f"filename_joined: `{filename_joined}`")
    _mo1 = mo.md(f"""The base directory (pm.location) is then combined with the filename 'components' to give the following -  
    Output directory:""")


    # The string in in this function is an example filename for a data file from the JAI camera
    _output_dir = str(pm.location) + '/' + pm.get_file_placement(filename_joined)


    _mo2 = mo.md(f"`{_output_dir}`")
    mo.vstack([_mo0, _mo1, _mo2])
    return


@app.cell
def _(mo, pm):

    filename_csv = "2025-08-15_06-30-03_400000_jai1_run-001.csv"  # notice, no timezone in the filename, so base_timezone conversion to output_timezone is assumed
    _mo0 = mo.md(f"filename_csv: `{filename_csv}`")
    _mo1 = mo.md(f"""This example shows the output for a `.csv` file. It has a seperate section in the `template.yaml` file, so the components may be extracted using different regex rules.  
    Using this capability, notice that the `sensor` and the `site_fn` have been switched in the filename, but the directory output is the same as the `.bin` file above.  
    Output directory: """)
    _output_dir = str(pm.location) + '/' + pm.get_file_placement(filename_csv)
    _mo2 = mo.md(f"`{_output_dir}`")


    mo.vstack([_mo1, _mo2])
    return


if __name__ == "__main__":
    app.run()
