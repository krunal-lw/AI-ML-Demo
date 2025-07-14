import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.title('Part 1')

file = st.file_uploader('Upload a file' , type=['csv'])

def display_correlation_matrix(df):
    st.subheader("Correlation Matrix")
    
    if df is None:
        st.warning("Need at least 2 numeric columns for correlation matrix.")
        return
    # sns.heatmap(corr_matrix)
    fig, ax = plt.subplots(figsize=(8, 4)) # Adjust figsize as needed
    sns.heatmap(df, annot=True, fmt=".2f", ax=ax)
    st.pyplot(fig)
    
    st.subheader("Correlation Values")
    st.dataframe(df.style.format("{:.4f}"), use_container_width=True)

# --------------------------------------------------------------------------------------------------------------
def get_numeric_df(df):
    return df.select_dtypes(include=['float64', 'int64'])
     

def display_mean_median_mode(df):
    st.subheader('Mean , Median and , Mode')
    df = get_numeric_df(df)
    stat = pd.DataFrame({
        'Mean': df.mean(),
        'Median': df.median(),
        'Mode': df.mode().iloc[0]
    })
    # st.subheader("Mean, Median, and Mode")
    st.dataframe(stat, use_container_width=True)

def display_descriptive_stats(df):
    st.subheader("Descriptive Statistics")
    
    desc_stats = df.describe()
    st.dataframe(desc_stats, use_container_width=True)


# --------------------------------------------------------------------------------------------------
with st.container(border=True):

    if file:
        df  = pd.read_csv(file)

        selected_columns = st.sidebar.multiselect('Select a column' , df.columns)

        st.markdown('### Selected Columns')

        st.dataframe(df[selected_columns])

        numeric_columns = get_numeric_df(df).columns

        
        filter_data = df.copy()

        if numeric_columns.any():

            st.sidebar.subheader('Numeric Filters')

            for column in numeric_columns:
                min_val = int(filter_data[column].min())
                max_val = int(filter_data[column].max())
                
                col_range = st.sidebar.slider(
                    f'Filter {column}',
                    min_val,
                    max_val,
                    (min_val, max_val)
                )
                
                filter_data = filter_data[filter_data[column].between(col_range[0], col_range[1])]
        
        st.subheader('Data Statistics')

        if selected_columns:
            st.dataframe(filter_data[selected_columns].describe())
        else:
            st.dataframe(filter_data.describe())
        
        st.subheader('Filtered Data')

        if selected_columns:
            st.dataframe(filter_data[selected_columns])
        else:
            st.dataframe(filter_data)


if file:
    st.title('Part 2')

    with st.container(border=True):
        st.subheader('Data Preview')

        st.dataframe(df)
        st.markdown(f'##### Shape of Dataset : {df.shape}')
        st.markdown(f'##### Columns : {[i for i in df.columns]}')
        st.markdown(f'##### Missing Values : {df.isnull().sum().sum()}')

        display_descriptive_stats(df)

        display_mean_median_mode(df)


        display_correlation_matrix(get_numeric_df(df).corr())

