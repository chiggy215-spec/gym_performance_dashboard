Gym Performance Dashboard
Overview
This project is an interactive Streamlit dashboard designed to track summer gym performance across regions, districts, and individual gyms. The dashboard analyzes new member growth and personal training (PT) session sales, comparing current-year performance against the prior year and measuring progress toward defined summer goals.
The dashboard automatically reads data from an Excel file stored within this repository, ensuring the application stays synchronized with the latest dataset.

Key Features
1. Summer Membership Goal Tracking
  •	Tracks new member acquisitions for the summer period (June 1 – August 31).
  •	Calculates a summer target equal to 110% of the prior year’s total summer memberships.
  •	Displays progress using a goal gauge visualization showing:
    o	Current progress
    o	Target threshold
    o	Projected end-of-summer total
   
3. Projection Modeling
A projection model estimates the final summer membership total based on current progress compared to the same point in the prior year.
Projection logic:
  •	Calculates how far through the summer season the current data is
  •	Compares that progress to the prior year's pace
  •	Projects the final total if the current trend continues
Key outputs:
  •	Projected summer total
  •	Variance to target
  •	Progress toward summer goal

4. Year-over-Year Trend Visualization
A cumulative line chart compares daily membership growth between years by overlaying both years on the same calendar axis (MM/DD). This allows quick comparison of whether current performance is ahead or behind last year’s pace.

5. Personal Training Sales Tracking
The dashboard tracks total personal training sessions sold and compares them year-over-year.

Additional KPI insight:
  •	 PT Sessions per Member
  •	Helps determine whether PT growth is driven by:
    o	More members
    o	Higher engagement per member

5. Performance Leaderboards
Performance is analyzed across organizational levels:

  Gyms
    •	Top performing gyms
    •	Bottom performing gyms
    •	Performance vs target %

  Districts
    •	Current vs prior year performance
    •	Target attainment

  Regions
    •	Regional performance summaries
    •	Visual bullet charts showing progress vs targets

6. Interactive Filters
Users can dynamically filter results by:

   •	Region
   •	District
   •	Gym
   •	Date range

KPIs, projections, and targets automatically update based on the selected filters.

Data Source
The dashboard reads from an Excel dataset included in this repository.
Example data fields include:

  •	start_dt — membership start date
  •	cust_type — new vs existing member
  •	region — regional grouping
  •	district — district grouping
  •	store_nbr — gym location identifier
  •	prod_cnt — personal training sessions sold
  
Technology Stack
•	Python
•	Streamlit
•	Pandas
•	NumPy
•	Plotly

These tools power the interactive dashboard, data processing, and visualizations.

Running the Dashboard
1.	Clone the repository:
  git clone https://github.com/yourusername/gym_performance_dashboard.git
2.	Install dependencies:
  pip install -r requirements.txt
3.	Run the Streamlit application:
  streamlit run streamlit_app.py

Author
This project was developed as part of a gym performance analytics initiative to help leadership monitor operational performance and sales activity across multiple locations.

