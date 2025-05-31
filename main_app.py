import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.data.storage import (
    Channel, Video, Base, 
    get_channel_subscriber_history, 
    get_channel_view_history, 
    get_video_view_history,
    get_channel_video_publication_dates
)
import plotly.graph_objects as go
from datetime import datetime

DB_PATH = "sqlite:///data/youtube.db"
engine = create_engine(DB_PATH)
Session = sessionmaker(bind=engine)

st.title("📺 YouTube Dashboard")

def get_channels():
    with Session() as sess:
        return sess.query(Channel).all()

def get_videos_for_channel(channel_id, only_hidden=False):
    with Session() as sess:
        return sess.query(Video).filter(Video.channel_id == channel_id, Video.hidden == only_hidden).order_by(Video.published_at.desc()).all()

def create_evolution_chart(history_data, video_publications, title, y_label, color="#4ecdc4"):
    """Create evolution chart with video publication markers"""
    if not history_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No historical data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        fig.update_layout(title=title, height=400)
        return fig
    
    # Prepare data
    df_history = pd.DataFrame(history_data)
    df_history['date'] = pd.to_datetime(df_history['date'])
    df_history = df_history.sort_values('date')
    
    # Create main chart
    fig = go.Figure()
    
    # Evolution line
    fig.add_trace(go.Scatter(
        x=df_history['date'],
        y=df_history['count'],
        mode='lines+markers',
        name=y_label,
        line=dict(color=color, width=3),
        marker=dict(size=6, color=color),
        hovertemplate=f'<b>%{{y:,.0f}}</b> {y_label.lower()}<br>%{{x}}<extra></extra>'
    ))
    
    # Add video publication markers
    if video_publications:
        video_dates = []
        video_titles = []
        video_y_values = []
        
        for video in video_publications:
            video_date = pd.to_datetime(video['date'])
            # Interpolate Y value for video date
            if len(df_history) > 1:
                # Find interpolated value
                if video_date <= df_history['date'].min():
                    y_val = df_history['count'].iloc[0]
                elif video_date >= df_history['date'].max():
                    y_val = df_history['count'].iloc[-1]
                else:
                    # Linear interpolation
                    idx = df_history[df_history['date'] <= video_date].index[-1]
                    if idx < len(df_history) - 1:
                        x1, y1 = df_history.loc[idx, 'date'], df_history.loc[idx, 'count']
                        x2, y2 = df_history.loc[idx + 1, 'date'], df_history.loc[idx + 1, 'count']
                        # Interpolation
                        ratio = (video_date - x1) / (x2 - x1)
                        y_val = y1 + ratio * (y2 - y1)
                    else:
                        y_val = df_history.loc[idx, 'count']
            else:
                y_val = df_history['count'].iloc[0] if len(df_history) > 0 else 0
            
            video_dates.append(video_date)
            video_titles.append(video['title'][:50] + "..." if len(video['title']) > 50 else video['title'])
            video_y_values.append(y_val)
        
        # Add video markers
        fig.add_trace(go.Scatter(
            x=video_dates,
            y=video_y_values,
            mode='markers',
            name='Video Publication',
            marker=dict(
                size=12,
                color='red',
                symbol='diamond',
                line=dict(width=2, color='darkred')
            ),
            text=video_titles,
            hovertemplate='<b>📹 %{text}</b><br>%{x}<br>%{y:,.0f} ' + y_label.lower() + '<extra></extra>'
        ))
    
    # Formatting
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        xaxis_title="Date",
        yaxis_title=y_label,
        height=400,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis=dict(tickformat=',')
    )
    
    return fig

def create_video_evolution_chart(video_history, video_title):
    """Create evolution chart for a specific video's views"""
    if not video_history:
        fig = go.Figure()
        fig.add_annotation(
            text="No historical data available for this video",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=14)
        )
        fig.update_layout(title=f"📈 View Evolution - {video_title[:50]}...", height=350)
        return fig
    
    # Prepare data
    df_history = pd.DataFrame(video_history)
    df_history['date'] = pd.to_datetime(df_history['date'])
    df_history = df_history.sort_values('date')
    
    # Create chart
    fig = go.Figure()
    
    # Evolution line
    fig.add_trace(go.Scatter(
        x=df_history['date'],
        y=df_history['count'],
        mode='lines+markers',
        name='Views',
        line=dict(color='#45b7d1', width=3),
        marker=dict(size=6, color='#45b7d1'),
        fill='tonexty',
        fillcolor='rgba(69, 183, 209, 0.1)',
        hovertemplate='<b>%{y:,.0f}</b> views<br>%{x}<extra></extra>'
    ))
    
    # Calculate growth if we have more than one point
    if len(df_history) > 1:
        growth = int(df_history['count'].iloc[-1] - df_history['count'].iloc[0])
        growth_percent = (growth / df_history['count'].iloc[0] * 100) if df_history['count'].iloc[0] > 0 else 0
        
        subtitle = f"Growth: +{growth:,} views ({growth_percent:+.1f}%)"
    else:
        subtitle = ""
    
    # Formatting
    fig.update_layout(
        title=dict(
            text=f"📈 View Evolution - {video_title[:50]}{'...' if len(video_title) > 50 else ''}<br><sub>{subtitle}</sub>",
            font=dict(size=14)
        ),
        xaxis_title="Date",
        yaxis_title="Number of Views",
        height=350,
        hovermode='x',
        showlegend=False,
        yaxis=dict(tickformat=',')
    )
    
    return fig

# === SIDEBAR ===
channels = get_channels()
st.sidebar.title("Channel List")

selected_channel_id = st.sidebar.radio(
    "Click on a channel to see videos",
    [ch.id for ch in channels],
    format_func=lambda ch_id: next((ch.title for ch in channels if ch.id == ch_id), "Unknown")
)

# === MAIN ===
if selected_channel_id:
    ch = next((c for c in channels if c.id == selected_channel_id), None)
      
    st.header(ch.title)

    if st.button("🗑️ Delete this channel", key=f"del_{ch.id}"):
        st.session_state["delete_confirm_channel_id"] = ch.id

    st.write(f"Description: {ch.description}")
    st.write(f"Subscribers: {ch.subscribers or 'N/A'}")

    # === EVOLUTION CHARTS FOR THE CHANNEL ===
    st.subheader("📊 Channel Evolution")
    
    # Get historical data
    subscriber_history = get_channel_subscriber_history(ch.id)
    view_history = get_channel_view_history(ch.id)
    video_publications = get_channel_video_publication_dates(ch.id)
    
    # Subscribers chart
    fig_subscribers = create_evolution_chart(
        subscriber_history, 
        video_publications,
        "👥 Subscriber Evolution",
        "Subscribers",
        "#ff6b6b"
    )
    st.plotly_chart(fig_subscribers, use_container_width=True)
    
    # Total views chart
    fig_views = create_evolution_chart(
        view_history,
        video_publications,
        "👀 Total Views Evolution",
        "Total Views",
        "#4ecdc4"
    )
    st.plotly_chart(fig_views, use_container_width=True)
    
    # Channel deletion confirmation
    delete_id = st.session_state.get("delete_confirm_channel_id")
    if delete_id == ch.id:
        st.warning("⚠️ This action will permanently delete the channel AND all its videos. Are you sure?")
        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("Yes, delete", key=f"conf_del_{ch.id}"):
                with Session() as sess:
                    sess.query(Video).filter(Video.channel_id == ch.id).delete()
                    sess.query(Channel).filter(Channel.id == ch.id).delete()
                    sess.commit()
                st.success("Channel deleted!")
                st.session_state.pop("delete_confirm_channel_id")
                st.rerun()
        with col2:
            if st.button("Cancel", key=f"ann_{ch.id}"):
                st.session_state.pop("delete_confirm_channel_id")

    show_hidden = st.checkbox("Show hidden videos", value=False)
    videos = get_videos_for_channel(ch.id, only_hidden=show_hidden)
    st.subheader(f"Videos ({len(videos)})")

    data = []
    for vid in videos:
        data.append({
            "Title": vid.title,
            "Date": vid.published_at.strftime("%Y-%m-%d"),
            "Views": vid.view_count,
            "Likes": vid.like_count,
            "Like Ratio": f"{(vid.like_count / vid.view_count * 100):.2f}%" if vid.view_count else "-",
            "Comments": vid.comment_count,
            "Link": f"https://www.youtube.com/watch?v={vid.id}",
            "ID": vid.id,
        })
    
    df = pd.DataFrame(data)
    
    # Column configuration with clickable links
    column_config = {
        "Link": st.column_config.LinkColumn(
            "YouTube Link",
            help="Click to open the video",
            validate="^https://.*",
            max_chars=100,
            display_text="▶️ Watch"
        ),
        "ID": None,
    }
    
    # Main table
    event = st.dataframe(
        df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        selection_mode="single-row",
        on_select="rerun",
        key="video_table"
    )
    
    # Selection handling
    selected_rows = event.selection.rows
    
    if selected_rows:
        selected_idx = selected_rows[0]
        selected_video = videos[selected_idx]
        
        # Card with selected video info
        with st.container():
            st.markdown("---")
            st.subheader("🎯 Selected Video")
            
            # Display details in columns
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**📺 {selected_video.title}**")
                st.caption(f"Published on {selected_video.published_at.strftime('%d/%m/%Y')}")
                if hasattr(selected_video, 'description') and selected_video.description:
                    with st.expander("📝 Description"):
                        # Length and copy button row
                        col_info, col_copy = st.columns([3, 1])
                        
                        with col_info:
                            st.caption(f"📏 {len(selected_video.description)} characters")
                        
                        with col_copy:
                            if st.button("📋", help="Copy description", key=f"copy_desc_{selected_video.id}"):
                                st.code(selected_video.description, language=None)
                                st.success("✅ Description copied above!")
                        
                        # Scrollable styled container
                        st.markdown(
                            f"""
                            <div style="
                                max-height: 250px; 
                                overflow-y: auto; 
                                padding: 15px; 
                                border: 1px solid #ddd; 
                                border-radius: 8px;
                                background-color: #fafafa;
                                font-family: inherit;
                                line-height: 1.6;
                                white-space: pre-wrap;
                            ">
                            {selected_video.description}
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
            
            with col2:
                st.metric("👀 Views", f"{selected_video.view_count:,}")
                st.metric("👍 Likes", f"{selected_video.like_count:,}")
                st.metric("💬 Comments", f"{selected_video.comment_count:,}")

            # --- STATISTICS SECTION ---
            st.subheader("📊 Statistics")
            
            # Basic calculations
            engagement = (selected_video.like_count + selected_video.comment_count) / selected_video.view_count * 100 if selected_video.view_count > 0 else 0
            like_percent = selected_video.like_count / selected_video.view_count * 100 if selected_video.view_count > 0 else 0
            comment_percent = selected_video.comment_count / selected_video.view_count * 100 if selected_video.view_count > 0 else 0
            
            # Basic metrics
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            with col_stat1:
                st.metric(
                    label="🎯 Engagement",
                    value=f"{engagement:.2f}%",
                    help="(Likes + Comments) / Views"
                )
            
            with col_stat2:
                st.metric(
                    label="👍 Like Rate",
                    value=f"{like_percent:.3f}%",
                    help="Likes / Views"
                )
            
            with col_stat3:
                st.metric(
                    label="💬 Comment Rate", 
                    value=f"{comment_percent:.3f}%",
                    help="Comments / Views"
                )
            
            # --- DETAILED ANALYSIS ---
            details_key = f"show_details_{selected_video.id}"
            if details_key not in st.session_state:
                st.session_state[details_key] = False
            
            # Toggle button for details
            if st.button(
                f"🔢 {'Hide' if st.session_state[details_key] else 'Show'} details {'⬆️' if st.session_state[details_key] else '⬇️'}", 
                key=f"toggle_details_{selected_video.id}"
            ):
                st.session_state[details_key] = not st.session_state[details_key]
                st.rerun()
            
            # Conditional display of detailed analysis
            if st.session_state[details_key]:
                with st.container():
                    st.markdown("---")
                    st.subheader("📈 Detailed Analysis")
                    
                    # === VIDEO VIEW EVOLUTION CHART ===
                    video_view_history = get_video_view_history(selected_video.id)
                    fig_video_evolution = create_video_evolution_chart(video_view_history, selected_video.title)
                    st.plotly_chart(fig_video_evolution, use_container_width=True)
                    
                    # Advanced metrics
                    st.subheader("🔢 Advanced Metrics")
                    
                    col_detail1, col_detail2, col_detail3, col_detail4 = st.columns(4)
                    
                    with col_detail1:
                        st.metric(
                            label="👥 Total Views",
                            value=f"{selected_video.view_count:,}",
                            help="Total number of views"
                        )
                    
                    with col_detail2:
                        like_ratio = selected_video.like_count / selected_video.view_count * 1000 if selected_video.view_count > 0 else 0
                        st.metric(
                            label="👍 Likes/1000 views",
                            value=f"{like_ratio:.1f}",
                            help="Number of likes per 1000 views"
                        )
                    
                    with col_detail3:
                        comment_ratio = selected_video.comment_count / selected_video.view_count * 1000 if selected_video.view_count > 0 else 0
                        st.metric(
                            label="💬 Comments/1000 views",
                            value=f"{comment_ratio:.1f}",
                            help="Number of comments per 1000 views"
                        )
                    
                    with col_detail4:
                        if selected_video.like_count > 0:
                            comment_like_ratio = selected_video.comment_count / selected_video.like_count
                            st.metric(
                                label="🗣️ Comments/Like",
                                value=f"{comment_like_ratio:.2f}",
                                help="Ratio of comments per like"
                            )
                        else:
                            st.metric(
                                label="🗣️ Comments/Like",
                                value="N/A",
                                help="No likes to calculate ratio"
                            )
                    
                    # Temporal analysis
                    st.subheader("📅 Temporal Analysis")
                    
                    days_since_publish = (pd.Timestamp.now() - selected_video.published_at).days
                    
                    col_time1, col_time2, col_time3 = st.columns(3)
                    
                    with col_time1:
                        st.metric(
                            label="📅 Days since publication",
                            value=f"{days_since_publish}",
                            help="Age of the video"
                        )
                    
                    with col_time2:
                        if days_since_publish > 0:
                            views_per_day = int(selected_video.view_count / days_since_publish)
                            st.metric(
                                label="👁️ Views/day",
                                value=f"{views_per_day:,}",
                                help="Average views per day"
                            )
                        else:
                            st.metric("👁️ Views/day", "N/A")
                    
                    with col_time3:
                        if days_since_publish > 0:
                            interactions_per_day = (selected_video.like_count + selected_video.comment_count) / days_since_publish
                            st.metric(
                                label="⚡ Interactions/day",
                                value=f"{interactions_per_day:.1f}",
                                help="Average interactions per day"
                            )
                        else:
                            st.metric("⚡ Interactions/day", "N/A")
            
            st.markdown("---")
            
            # Personal analysis section
            st.subheader("📊 Personal Analysis")
            
            has_analysis = hasattr(selected_video, 'analysis') and selected_video.analysis
            
            # Initialize editor states
            if f"edit_mode_{selected_video.id}" not in st.session_state:
                st.session_state[f"edit_mode_{selected_video.id}"] = not has_analysis
            
            # Template for analysis
            template = f"""# Video Analysis: {selected_video.title}

## Strengths
- 
- 
- 

## Areas for Improvement
- 
- 
- 

## Why this video performed {'well' if engagement > 5 else 'less well'}?
- 

## Ideas to Reproduce
- 

## Personal Notes
- 
"""
            
            # Container for analysis
            with st.container():
                # Top toolbar
                col_toggle, col_spacer, col_delete = st.columns([2, 8, 2])
                
                with col_toggle:
                    edit_mode = st.session_state[f"edit_mode_{selected_video.id}"]
                    if has_analysis and not edit_mode:
                        if st.button("📝 Edit", key=f"toggle_edit_{selected_video.id}", use_container_width=True):
                            st.session_state[f"edit_mode_{selected_video.id}"] = True
                            st.rerun()
                
                with col_delete:
                    if has_analysis:
                        if st.button("🗑️ Delete", key=f"delete_analysis_{selected_video.id}", use_container_width=True):
                            st.session_state[f"confirm_delete_analysis_{selected_video.id}"] = True
                            st.rerun()
                
                # Analysis deletion confirmation
                if st.session_state.get(f"confirm_delete_analysis_{selected_video.id}", False):
                    st.warning("⚠️ Are you sure you want to delete the analysis for this video?")
                    col_conf1, col_conf2 = st.columns(2)
                    with col_conf1:
                        if st.button("✅ Confirm", key=f"confirm_del_analysis_{selected_video.id}"):
                            with Session() as sess:
                                sess.query(Video).filter(Video.id == selected_video.id).update({"analysis": None})
                                sess.commit()
                            st.success("Analysis deleted!")
                            st.session_state.pop(f"confirm_delete_analysis_{selected_video.id}")
                            st.session_state[f"edit_mode_{selected_video.id}"] = True
                            st.rerun()
                    with col_conf2:
                        if st.button("❌ Cancel", key=f"cancel_del_analysis_{selected_video.id}"):
                            st.session_state.pop(f"confirm_delete_analysis_{selected_video.id}")
                            st.rerun()
                
                # Analysis content (edit or display)
                if has_analysis:
                    if st.session_state[f"edit_mode_{selected_video.id}"]:
                        # Edit mode
                        analysis_text = st.text_area(
                            "Your analysis:",
                            value=selected_video.analysis,
                            height=400,
                            key=f"analysis_text_{selected_video.id}",
                            label_visibility="collapsed"
                        )
                        
                        col_save, col_cancel = st.columns([2, 10])
                        with col_save:
                            if st.button("💾 Save", key=f"save_analysis_{selected_video.id}", use_container_width=True):
                                with Session() as sess:
                                    sess.query(Video).filter(Video.id == selected_video.id).update({"analysis": analysis_text})
                                    sess.commit()
                                st.success("Analysis saved successfully!")
                                st.session_state[f"edit_mode_{selected_video.id}"] = False
                                st.rerun()
                    else:
                        # Display mode - use a styled container
                        with st.container():
                            st.markdown(
                                """
                                <style>
                                .analysis-container {
                                    padding: 15px;
                                    border: 1px solid #ddd;
                                    border-radius: 8px;
                                    background-color: #f8f9fa;
                                }
                                </style>
                                """,
                                unsafe_allow_html=True
                            )
                            
                            # Use a div with class for styling
                            st.markdown('<div class="analysis-container">', unsafe_allow_html=True)
                            
                            # Render markdown directly to preserve formatting
                            st.markdown(selected_video.analysis)
                            
                            # Close the div
                            st.markdown('</div>', unsafe_allow_html=True)
                else:
                    # No analysis, display editor with template
                    analysis_text = st.text_area(
                        "Your analysis:",
                        value=template,
                        height=400,
                        key=f"analysis_text_new_{selected_video.id}",
                        label_visibility="collapsed"
                    )
                    
                    col_save, col_spacer = st.columns([2, 10])
                    with col_save:
                        if st.button("💾 Save", key=f"save_new_analysis_{selected_video.id}", use_container_width=True):
                            with Session() as sess:
                                sess.query(Video).filter(Video.id == selected_video.id).update({"analysis": analysis_text})
                                sess.commit()
                            st.success("Analysis saved successfully!")
                            st.session_state[f"edit_mode_{selected_video.id}"] = False
                            st.rerun()
            
            # Action buttons
            st.subheader("⚡ Actions")
            col1, col2 = st.columns(2)
            
            with col1:
                if show_hidden:
                    if st.button("✅ Restore", key=f"restore_{selected_video.id}", use_container_width=True):
                        with Session() as sess:
                            sess.query(Video).filter(Video.id == selected_video.id).update({"hidden": False})
                            sess.commit()
                        st.success("Video restored!")
                        st.rerun()
                else:
                    if st.button("🙈 Hide", key=f"hide_{selected_video.id}", use_container_width=True):
                        with Session() as sess:
                            sess.query(Video).filter(Video.id == selected_video.id).update({"hidden": True})
                            sess.commit()
                        st.success("Video hidden!")
                        st.rerun()
            
            with col2:
                video_url = f"https://www.youtube.com/watch?v={selected_video.id}"
                st.link_button("🎥 Open", video_url, use_container_width=True)
    
    else:
        st.info("👆 Select a row in the table above to see available actions")