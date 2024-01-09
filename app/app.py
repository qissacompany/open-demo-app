#app.py
import streamlit as st
import pandas as pd
import datetime
import re
import open_utils, qissa_utils, viz

# --------- CLIENT CONFIGS ---------------
client_page_title = "Qissa Company Demo App"
client_bucket_url = st.secrets['client_bucket']['BUCKET_url']
bucket_name = st.secrets["client_bucket"]['BUCKET_name']
client_logo_url = "https://" + client_bucket_url + "/" + bucket_name + '/media/Q-logo_black.png'
default_lang = "FIN"

client_bg_image_url = "https://" + client_bucket_url + "/" + bucket_name + "/appbackgrounds/background_01.png"

#page configs
st.set_page_config(page_title=client_page_title, layout="wide", initial_sidebar_state='collapsed',
                page_icon="✨",
                menu_items={"Get help":None,
                            "Report a bug":None,
                            "About": "Sanely Simple Urban Metrics By https://qissa.fi"})
# custom feature configs
st.markdown("""
<style>
div.stButton > button:first-child {
    background-color: #fab43a;
    color:#ffffff;
}
div.stButton > button:hover {
    background-color: #e75d35; 
    color:#ffffff;
    }
[data-testid="stMetricDelta"] svg {
        display: none;}
.stProgress .st-bo {
    background-color: green;
}
</style>
""", unsafe_allow_html=True)

#background
def add_bg_image(bg_image_url=None):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: url({bg_image_url});
            background-size: cover
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

add_bg_image(client_bg_image_url)


#LOCAT
client_name = ["[Qissa Oy](https://qissa.fi)",
               "[By Qissa Company](https://qissa.fi)"]
client_app_name = ["Demo V1","Demo App V1"]
qissa_footer_badge_text = ["Kaupunkiarkkitehtuurin_analytiikkaa",
                      "Urban_architectural_analytics"]
signin_text = ['Kirjaudu sisään!','Sign in!']

signed_in_title = ['Tervetuloa!','Welcome!']
signed_in_ingress = ['Tällä demolla voit testata miten helppoa on tarkastella kaavoituksen todellisia vaikutuksia!',
                     'With this demo app you can test how easy it is to analyze true urban design impacts!']
signed_in_subingress = ['Jokainen projektiappi räätälöidään asiakkaan tai hankkeen graafisen ilmeen ja analyysitarpeiden mukaan. :ok_hand:',
                        'Each project app is tailored & updated by the brand image and analysis needs of the client or project. :ok_hand:']

tab_titles = [['Väestökasvu','Ihmisvirrat','Hiilijalanjälki','..Tai mikä vain asiakaskohtainen analyysitarve!'],
              ['Population growth','People flows','Corbon footprint','..Or any client based analytics you need!']]

not_plan_warning = [':point_up: Tee tai tuo ensin suunnitelma!',':point_up: Upload or create a plan to get base analytics!']
not_available_warning = ['Lisää analytiikkateemoja tarpeen mukaan! :muscle:',
                         'Get more analytics in your app as needed! :muscle:']
more_info_text = ['Pyydä lisätietoja tai sovi esittely :point_right: office@qissa.fi',
                  'For more info ask anything :point_right: office@qissa.fi']

# ------- HEADER -----------

logo_holder = st.empty()
header_holder = st.empty()
client_name_holder = st.empty()
lang_holder = st.empty()

#lang toggle
with lang_holder:
    if default_lang == "FIN":
        lang = st.toggle('ENG')
        if lang:
            lin = 1
        else:
            lin = 0
    else:
        lang = st.toggle('FIN')
        if lang:
            lin = 0
        else:
            lin = 1

#header info
logo_holder.image(client_logo_url,width=150)
header_holder.header(client_app_name[lin],divider="orange")
client_name_holder.markdown(f"**{client_name[lin]}**")

st.markdown('###')
singin_holder = st.container()

#check campaign & auth
url_params = st.experimental_get_query_params()
try:
    campaign = url_params.get('campaign')[0]
except:
    campaign = False

if not campaign:
    auth_check = open_utils.check_password(lin=lin)
    if not auth_check:
        singin_holder.subheader(signin_text[lin])
    else:
        with singin_holder:
            st.subheader(signed_in_title[lin])
            st.subheader(signed_in_ingress[lin])
            st.markdown(signed_in_subingress[lin])
            st.markdown('###')
else:
    auth_check = True

# ------- CLIENT CONTENT -----------

if auth_check:
    if campaign:
        if not open_utils.check_test_query_count(max=25,lin=lin):
            st.stop()

    #LOCAT

    #loader
    data_source_expander_title = ['Suunnitelmatieto','Urban design data']
    data_source_selector = ['','']
    plan_selection = ['Lataa viitesuunnitelma','Load master plan']
    slider_selection = ['Tee mitoituskonsepti','Prepare volume concept']
    file_uploader_title = ['Lataa suunnitelma','Load plan']
    uploaded_file_warning_zip = ["Suunnitelma tulee olla shapefile muodossa ('buildings.shp'/'network.shp') pakattuna zip-tiedostoon.",
                                 "Plan must be in shapefile-format ('buildings.shp'/'network.shp') in zip-file"]
    uploaded_file_warning_buildings = ['Ei rakennuksia datassa',
                                        'No buildings in data']
    uploaded_file_warning_network = ['Ei verkostoa datassa',
                                        'No network in data']
    use_demo_plan_text = ['Käytä demosuunnitelmaa','Use demo plan']
    
    #for sliders
    volume_concept_title = ['Mitoitussuunnitelma','Volume plan']
    one_family_house_vol_title = ['Pientalojen kokonaismitoitus (kem²)','One-family-house volume (GFAm²)']
    multi_family_house_vol_title = ['Rivitalojen kokonaismitoitus (kem²)','Multi-family-house volume (GFAm²)']
    apartment_building_vol_title = ['Kerrostalojen kokonaismitoitus (kem²)','Apartment building volume (GFAm²)']
    one_family_house_pro_title = ['Pientalojen hankekoko','One-family-house project size']
    multi_family_house_pro_title = ['Rivitalojen hankekoko','Multi-family-house project size']
    apartment_building_pro_title = ['Kerrostalojen hankekoko','Apartment building project size']
    num_of_con_companies_title = ["Samanaikainen tuotanto","Paraller construction"]
    pre_con_and_sim_time_title = ['Esirakentamis- ja simulointiaika','Preconstruction and simulation time']

    #for policy
    unit_size_policy_selection = ['Käytä asuntokoon ohjauspolitiikkaa','Apply unit size policy']
    policy_string_error = ['Politiikkamuotoilu on väärin','Policy statement is malformed']
    unit_size_range_error = ['Asuntokoot on oltava 25-100 m2 ja prosentit yht. max 100%','Unit size range is 25-100 m2 and percentage sum max 100']
    policy_input_title = ['Politiikkamuotoilu','Policy statement']
    policy_caption_text = ['Muuta numeroita, mutta pidä muotoilu samana.','Refine numbers but keep the format.']
    
    #for uploaded data
    building_type_info = ['Rakennustyyppitieto','Building type info']
    building_GFA_info = ['Kerrosalatieto','GFA info']
    one_family_house_col_selection = ['Pientalot =','One-family-houses =']
    multi_family_house_col_selection = ['Rivitalot =','Multi-family-houses =']
    apartment_building_col_selection = ['Kerrostalot =','Apartment buildings =']
    no_value_text = ['Ei asetettu','Not defined']
    cols_set_checkbox_title = ['Tiedot asetettu','Data source ok']
    fix_value_sources_text = ['Korjaa tietolähteet','Fix data sources']

    #for analysis
    analysis_part_subheader = ['Analyysit','Analysis']
    no_data_source_warning = ['Datalähdettä ei ole valittu.','No data source set']
    no_residential_buildings = ['Ei asuinrakennuksia','No residential buildings']
    run_analysis_button = ['Tee analyysi','Run analysis']
    pop_sim_expander_title = ['Rakentaminen ja väestökehitys','Construction and population growth']
    sim_data_expander_title = ['Simulointidata','Simulation data']

    #for metrics
    pop_growth_text = ['Väestökasvu','Population growth']
    avg_unit_size_title = ['Asuntojen keskikoko','Average unit size']
    segregation_index = ['Segregaatioindeksi','Segregation index']
    custom_metric_text = ['Tai mikä vain asiakaskohtainen mittari..','Or any client based metrics..']

    #data source expander
    with st.expander(data_source_expander_title[lin], expanded=True):
        ds1, ds2 = st.columns(2)
        data_source_selection = ds1.radio(data_source_selector[lin],[slider_selection[lin],plan_selection[lin]])
        
        uploaded_file = None
        residential_buildings_dict = None
        network = None

        #data source
        if data_source_selection == plan_selection[lin]:
            uploaded_file = ds2.file_uploader(file_uploader_title[lin], type=['zip'], key='uploaded')
            use_demo_plan = ds2.checkbox(use_demo_plan_text[lin])

            #func to prep data for api
            def plan_to_dict(buildings_in,my_type,my_gfa,type_value_dict):
                buildings = buildings_in.copy()
                buildings.replace({my_type: type_value_dict}, inplace=True)
                buildings.rename(columns={my_type:'type',my_gfa:'gfa'}, inplace=True)
                residential_list = ['one-family-house','multi-family-house','apartment-condo']
                residential_buildings_df = buildings.loc[buildings['type'].isin(residential_list)]
                #convert to dict for api
                cols_for_dict = ['type','gfa']
                residential_buildings_dict = residential_buildings_df[cols_for_dict].to_dict(orient='records')
                return residential_buildings_dict
            
            if uploaded_file is not None:
                # Get the file extension and check its type
                file_type = uploaded_file.type
                if "zip" in file_type:

                    # check if buildings available in zip..
                    try:
                        buildings, plan_name = qissa_utils.extract_shapefiles_and_filenames_from_zip(uploaded_file,'Polygon')

                    except Exception as err_bu:
                        print(f"Buildings data error: {err_bu}")
                        st.warning(uploaded_file_warning_buildings[lin])

                    # check if network available in zip..
                    try:
                        network, net_name = qissa_utils.extract_shapefiles_and_filenames_from_zip(uploaded_file,'LineString')
                    except Exception as err_net:
                        print(f"Network data error: {err_net}")
                        st.warning(uploaded_file_warning_network[lin])
                else:
                    st.warning(uploaded_file_warning_zip[lin])
                
                #check extracted..
                if any(v is None for v in [buildings, plan_name]):
                    st.warning(uploaded_file_warning_zip[lin])
                    st.stop()
                    
                #set ups
                st.subheader(plan_name)
                s1,s2 = st.columns(2)
                map_holder = s2.empty()

                #define plan data
                col_list_all = buildings.drop(columns='geometry').columns.tolist()
                col_list_all.insert(0,no_value_text[lin])
                my_type = s1.selectbox(building_type_info[lin],col_list_all)
                my_gfa = s1.selectbox(building_GFA_info[lin],col_list_all)
                if my_type != no_value_text[lin]:
                    s1.markdown(f'**{my_type}**')
                    type_value_list = buildings[my_type].unique().tolist()
                    type_value_list.insert(0,no_value_text[lin])
                    one_family_house_value = s1.selectbox(one_family_house_col_selection[lin],type_value_list)
                    multi_family_house_value = s1.selectbox(multi_family_house_col_selection[lin],type_value_list)
                    apartment_condo_value = s1.selectbox(apartment_building_col_selection[lin],type_value_list)
                    num_comp = s1.slider(num_of_con_companies_title[lin], 1, 5, 2, step=1)
                    pre_con_sim_time = s1.slider(pre_con_and_sim_time_title[lin], 1, 30, [3,10], step=1)
                    cols_set = s1.checkbox(cols_set_checkbox_title[lin])
                
                    if cols_set:
                        try:
                            #prepare residential df for simulation
                            type_value_dict={one_family_house_value:'one-family-house',
                                            multi_family_house_value:'multi-family-house',
                                            apartment_condo_value:'apartment-condo'
                                            }
                            residential_buildings_dict = plan_to_dict(buildings_in=buildings,my_type=my_type,my_gfa=my_gfa, type_value_dict=type_value_dict)

                        except:
                            st.error(fix_value_sources_text[lin])
                    
                    #plot the plan
                    if my_gfa != no_value_text[lin]:
                        with map_holder:
                            fig_map = viz.plot_masterplan_map(bu=buildings,net=network, hover_columns=[my_type,my_gfa])
                            st.plotly_chart(fig_map, use_container_width=True, config = {'displayModeBar': False})

            #or use demo plan..
            if use_demo_plan and uploaded_file is None:
                st.markdown('---')
                #fetch demo file
                demo_file = qissa_utils.get_demo_file(demo_name='demo_plan_V1')
                buildings, plan_name = qissa_utils.extract_shapefiles_and_filenames_from_zip(demo_file,'Polygon')
                network, net_name = qissa_utils.extract_shapefiles_and_filenames_from_zip(demo_file,'LineString')
                fig_map = viz.plot_masterplan_map(bu=buildings,net=network, hover_columns=['kaava','kerrosala'])
                
                st.subheader('Demo')
                st.plotly_chart(fig_map, use_container_width=True, config = {'displayModeBar': False})
                
                #prep demo for api
                demo_type_value_dict={'ap':'one-family-house',
                                 'ar':'multi-family-house',
                                 'ak':'apartment-condo'
                                }
                d1,d2 = st.columns(2)
                num_comp = d1.slider(num_of_con_companies_title[lin], 1, 5, 2, step=1)
                pre_con_sim_time = d2.slider(pre_con_and_sim_time_title[lin], 1, 30, [3,20], step=1)
                residential_buildings_dict = plan_to_dict(buildings_in=buildings,my_type='kaava',my_gfa='kerrosala', type_value_dict=demo_type_value_dict)

        else: #using sliders..
            st.markdown('---')
            st.subheader(volume_concept_title[lin])
            s1,s2 = st.columns(2)    
            one_family_house_vol = s1.slider(one_family_house_vol_title[lin], 0, 10000, 2000, step=1000)
            one_family_house_pro = s2.slider(one_family_house_pro_title[lin], 50, 200, 120, step=10)
            multi_family_house_vol = s1.slider(multi_family_house_vol_title[lin], 0, 10000, 3000, step=1000)
            multi_family_house_pro = s2.slider(multi_family_house_pro_title[lin], 200, 2000, 500, step=100)
            apartment_condo_vol = s1.slider(apartment_building_vol_title[lin], 0, 20000, 6000, step=1000)
            apartment_condo_pro = s2.slider(apartment_building_pro_title[lin], 2000, 7000, 3000, step=1000)
            num_comp = s1.slider(num_of_con_companies_title[lin], 1, 5, 2, step=1)
            pre_con_sim_time = s2.slider(pre_con_and_sim_time_title[lin], 1, 30, [3,10], step=1)

            #volumes out as dict
            total_gfa_volumes = {
                'one-family-house': one_family_house_vol,
                'multi-family-house': multi_family_house_vol,
                'apartment-condo': apartment_condo_vol
                }
            project_sizes = {
                'one-family-house': one_family_house_pro,
                'multi-family-house': multi_family_house_pro,
                'apartment-condo': apartment_condo_pro
                }
            
            #func to gen projects from volumes
            def generate_projects(total_volumes: dict, project_sizes: dict):
                buildings = []

                for building_type, total_volume in total_volumes.items():
                    avg_project_size = project_sizes[building_type]
                    num_projects = total_volume // avg_project_size

                    for _ in range(num_projects):
                        buildings.append({
                            'type': building_type,
                            'gfa': avg_project_size
                        })
                
                return buildings
            
            # generate building projects from volumens
            residential_buildings_dict = generate_projects(total_gfa_volumes,project_sizes)
        
        #policy widget
        def unit_size_policy_maker_v1(lin=0):
            
            #LOCAT
            default_policy = ["Kerrostaloissa asunnoista 30 % tulee olla yli 40 m2 ja 20 % yli 80 m2. Pientaloissa asunnoista 50 % tulee olla yli 70 m2 ja 10 % yli 100 m2.",
                              "In apartment-condos 30 % of apartments must be over 40 m2 and 20 % over 80 m2. For multi/family-houses 50 % must be over 60 m2 and 10 % over 100 m2."]        
            policy_string = st.text_input(label=policy_input_title[lin],value=default_policy[lin],max_chars=150)
            st.caption(policy_caption_text[lin])

            def extract_numbers(input_string):
                numbers = re.findall(r'\b\d{1,3}\D?', input_string)
                return [int(re.findall(r'\d+', num)[0]) for num in numbers]
            
            my_policy_nums = extract_numbers(policy_string)
            
            def check_policy_numbers(numbers):
                if len(numbers) != 8:
                    st.warning(policy_string_error[lin])
                    st.stop()

                # Check x values for apartments (at indices 0 and 2)
                sum_x_values_apartments = numbers[0] + numbers[2]
                if any(x < 0 or x > 100 for x in [numbers[0], numbers[2]]) or sum_x_values_apartments > 100:
                    return False

                # Check x values for multi-family houses (at indices 4 and 6)
                sum_x_values_houses = numbers[4] + numbers[6]
                if any(x < 0 or x > 100 for x in [numbers[4], numbers[6]]) or sum_x_values_houses > 100:
                    return False

                # Check y values (at indices 1, 3, 5, 7)
                for i in range(1, len(numbers), 2):
                    if numbers[i] < 25 or numbers[i] > 100:
                        return False

                return True

            
            #check policy
            if not check_policy_numbers(my_policy_nums):
                st.warning(unit_size_range_error[lin])
                st.stop()

            my_unit_size_policy = {
                'apartment-condo': [my_policy_nums[0], my_policy_nums[1], my_policy_nums[2], my_policy_nums[3]],
                'multi-family-house': [my_policy_nums[4], my_policy_nums[5], my_policy_nums[6], my_policy_nums[7]]
            }
            return my_unit_size_policy
        
        #policy maker
        if residential_buildings_dict is not None and len(residential_buildings_dict) > 0:
            use_unit_size_policy = st.checkbox(unit_size_policy_selection[lin])
            if use_unit_size_policy:
                my_unit_size_policy = unit_size_policy_maker_v1(lin=lin)
            else:
                my_unit_size_policy = None

            


# --------------------- TABS ------------------------
    st.markdown("###")
    st.subheader(analysis_part_subheader[lin])
    tab1,tab2,tab3,tab4 = st.tabs(tab_titles[lin])

    with tab1:
        if residential_buildings_dict is not None and len(residential_buildings_dict) > 0:
            with st.expander(pop_sim_expander_title[lin],expanded=True):

                #params for api
                my_params = {
                    "buildings": residential_buildings_dict,
                    "sim_time_years": int(pre_con_sim_time[1]),
                    "pre_con_time": int(pre_con_sim_time[0]),
                    "construction_times": None,
                    "num_companies": int(num_comp),
                    "unit_size_policy": my_unit_size_policy,
                    "household_shares_estimates": None
                }

                CONSIM_respond = qissa_utils.consim_call(params=my_params)
                
                sim_df = pd.DataFrame(CONSIM_respond.get('body'))

                #plot
                st.plotly_chart(viz.simulation_plot(sim_df,lin=lin), use_container_width=True, config = {'displayModeBar': False})

                #check
                #st.data_editor(data=sim_df)

                #metrics
                tot_pop = sim_df[['families','singles','other']].sum(axis=1).sum()
                tot_gfa = sim_df['volume'].sum()
                plan_gfa = sum(item.get('gfa', 0) for item in residential_buildings_dict)
                cons_share = round(tot_gfa / plan_gfa * 100,2)
                avg_unit_size = round(sim_df.loc[sim_df['avg_unit_size'] != 0]['avg_unit_size'].mean(),0)

                #simpson div index
                def sdi(data: list):
                    #data as list { 'species': count } , returns the Simpson Diversity Index
                    def p(n, N):
                        if n is  0:
                            return 0
                        else:
                            return float(n)/N
                    N = sum(data.values())
                    return sum(p(n, N)**2 for n in data.values() if n != 0)
                
                #seg data
                families_sum = sim_df['families'].sum()
                single_and_others_sum = sim_df[['singles', 'other']].sum().sum()
                seg_data = {'families': families_sum, 'singles_and_other': single_and_others_sum}
                seg_ind = round((1-sdi(seg_data)),3) #inverted simpson
                seg_ero = round((0.5-seg_ind)*100,1)
                m1,m2,m3,m4 = st.columns(4)
                yr = ['v','yr']
                m1.metric(label=f"{pop_growth_text[lin]}, {pre_con_sim_time[1]} {yr[lin]}", value=f"{tot_pop:.0f}", delta=f"{cons_share:.0f} %") #m²
                m2.metric(label=avg_unit_size_title[lin],value=avg_unit_size)
                m3.metric(label=segregation_index[lin], value=f"{seg_ero}", delta=f"D={seg_ind}")
                m4.metric(label=custom_metric_text[lin], value=42, delta=+3.14)
                

                #more info
                st.success(more_info_text[lin])
        else:
             st.warning(not_plan_warning[lin])
        
            
    with tab2:
        st.warning(not_available_warning[lin])
    with tab3:
        st.warning(not_available_warning[lin])
    with tab4:
        st.warning(not_available_warning[lin])
    

#footer
st.markdown('###')
st.markdown('---')
copyright_text = ['&copy; Qissa kaupunkisuunnitteluanalytiikka Oy','&copy; Qissa Urban Analytics Company']
license = f'''
        <a href="https://qissa.fi" target="_blank">
            <img src="https://img.shields.io/badge/{qissa_footer_badge_text[lin]}-Qissa-fab43a" alt="Qissa Badge" title="{copyright_text[lin]}">
        </a>
        '''
st.markdown(license, unsafe_allow_html=True)