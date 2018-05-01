$(document).ready(function() {

  // Load the Visualization API and the corechart package.
  google.charts.load('current', {'packages':['corechart']});
  google.charts.load('current', {'packages':['bar']});
  google.charts.load('current', {'packages':['line']});

  var chart = chart_to_load;
  var team_data = JSON.parse(teams); //note this kills the order of the dict!!

  //when stats_breakdown.html loads home_stats
  //and away_stats will not necessarily be defined
  //hence the checks:
  if (typeof home_stats === 'undefined'){
    home_stats = null;
  }
  else{
    home_form = JSON.parse(home_stats);
  }

  if (typeof away_stats === 'undefined'){
    away_stats = null;
  }
  else{
    away_form = JSON.parse(away_stats);
  }

  //decide which chart to invoke
  switch(chart){
    case 'barChartGames':
      google.charts.setOnLoadCallback(drawChartWDL);
      break;
    case 'barChartPoints':
      google.charts.setOnLoadCallback(drawChartPts);
      break;
    case 'lineChart':
      console.log(team_data);
      google.charts.setOnLoadCallback(drawChartTrend);
      break;
    case 'pieChart':
      google.charts.setOnLoadCallback(drawChartPie);
  }//end switch

  //submit form when chart selected in drop-down list
  $('#chart_selection').change(function(){
    $('#chart_form').submit();
  });

  function drawChartWDL() {
    var data = new google.visualization.DataTable();
    //create the header row
    data.addColumn('string', 'Team');
    data.addColumn('number', 'Lost');
    data.addColumn('number', 'Drawn');
    data.addColumn('number', 'Won');
    //create data rows
    $.each(team_data, function(i,item){
      var chart_row = new Array();
      chart_row.push(i);
      chart_row.push(item[0]);
      chart_row.push(item[1]);
      chart_row.push(item[2]);
      data.addRow(chart_row);
    })
    //organise the teams by column 'Won'
    //from most wins to least wins
    data.sort([{column: 3, desc: true}]);

    //set up chart options
    var histogram_options = {
        animation: {"startup": true,
        duration: 1500,
        easing: 'out',},
        // width:1800,
        height:1000,
        chartArea:{
          left:180,top:50,width:'100%',
        },
        bar: { groupWidth: '61.8%' },
        isStacked: false,
        orientation: 'vertical',
        colors:['red', 'orange', 'green'],
        legend: { position: 'top', alignment:'center' },
      };
      var chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));
      chart.draw(data, google.charts.Bar.convertOptions(histogram_options));
  }; //end function drawChartWDL()

  function drawChartPts(){
    var data = new google.visualization.DataTable();
    //create the header row
    data.addColumn('string', 'Team');
    data.addColumn('number', 'Points Achieved');
    data.addColumn('number', 'Maximum Possible');
    data.addColumn({type: 'string', role: 'tooltip'});
    //create data rows
    $.each(team_data, function(i,item){
      var chart_row = new Array();
      chart_row.push(i);
      chart_row.push(item[3]);
      chart_row.push(item[4]);
      var max_possible = item[3] + item[4];
      chart_row.push(max_possible.toString());
      data.addRow(chart_row);
    })
    //organise the teams by column 'Points'
    //from highest points to lowest points
    data.sort([{column: 1, desc: true}]);
    //set up chart options
    var histogram_options = {
      animation: {"startup": true,
      duration: 1500,
      easing: 'out',},
      // width:1800,
      height:1000,
      chartArea:{
        left:75,top:50,width:'100%',
      },
      bar: { groupWidth: '61.8%' },
      isStacked: true,
      orientation: 'horizontal',
      colors:['green','blue'],
      legend: { position: 'top', alignment:'center' },
    };
    var chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));
    chart.draw(data, google.charts.Bar.convertOptions(histogram_options));
  }; //end function drawChartWDL()

  function drawChartTrend(){
    var weeks;
    $.each(team_data, function(i,item){
      // console.log("============================");
      // console.log(item.TeamName,i);
      // console.log(item.Positions,i);
      weeks = item.Positions.length;
      // console.log("============================");
      // header_row.push(item.TeamName);
    });

    //Create the data table.
    var data = new google.visualization.DataTable();
    //set up the header row, starting with the first column representing
    //the 'week'of the season and then adding a column for each team
    data.addColumn('number', 'Week');
    for (var team in team_data){
      data.addColumn('number', team_data[team].TeamName);
    }
    //create ROWs for chart data
    //create a row per week, the first col being the week number
    //and the other columns being each team's position for that week
    for (var week_count = 0; week_count < weeks; week_count++) {
      var chart_row = new Array();
      chart_row.push(week_count+1);
      $.each(team_data, function(i,item){
        chart_row.push(item.Positions[week_count]);
      })
      data.addRow(chart_row);
    }
    //set up chart options
    var options = {
      // width:1800,
      height:1000,
      title: 'Trend',
      legend: { position: 'bottom' },
      series: {
        1: {targetAxisIndex: 1},
        0: {targetAxisIndex: 0}
      },
      vAxes: {
          // Adds titles to each axis.
        0: {title: 'League Position'},
      },
      vAxis: {
        direction:-1,
        viewWindow: {
          min: 1,
          max: 20
        },
        ticks: [1, 4 , 8, 12, 16, 20]
      },
      hAxis: {
        maxValue:38,
        ticks: [2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38]
      },
      chartArea:{
        left:55,top:50,width:'90%',
      },
    };

    var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
    chart.draw(data, options);
  }//end function drawChartTrend

  function drawChartPie(){
    // Create the data table.
        var data_1 = new google.visualization.DataTable();
        data_1.addColumn('string', 'Result_Outcome');
        data_1.addColumn('number', 'Result_Count');
        data_1.addRow(['Wins', team_data['Won']]);
        data_1.addRow(['Draws', team_data['Drawn']]);
        data_1.addRow(['Losses', team_data['Lost']]);

        var data_2 = new google.visualization.DataTable();
        data_2.addColumn('string', 'Amount');
        data_2.addColumn('number', 'Amount');
        data_2.addRow(['Goals scored', team_data['GS']]);
        data_2.addRow(['Goals conceded', team_data['GC']]);

        var options_1 = { width:400,
                          height:300,
                          'pieHole': 0.5,
                          'colors': ['green', 'orange', 'red'],
                          chartArea: {left:5},
                          legend: { position: 'top', alignment:'center' },
                        };
        var options_2 = { width:400,
                          height:300,
                          'pieHole': 0.5,
                          'colors': ['green', 'red'],
                          chartArea: {left:5,},
                          legend: { position: 'top', alignment:'center' },
                        };
       var chart_1 = new google.visualization.PieChart(document.getElementById('WDL_chart'));
       var chart_2 = new google.visualization.PieChart(document.getElementById('goals_chart'));
       chart_1.draw(data_1, options_1);
       chart_2.draw(data_2, options_2);

    // Create home form data table
        var home_data = new google.visualization.DataTable();
        home_data.addColumn('string', 'Result_Outcome');
        home_data.addColumn('number', 'Result_Count');
        home_data.addRow(['Wins', home_form['Won']]);
        home_data.addRow(['Draws', home_form['Drawn']]);
        home_data.addRow(['Losses', home_form['Lost']]);

        var home_goals_data = new google.visualization.DataTable();
        home_goals_data.addColumn('string', 'Amount');
        home_goals_data.addColumn('number', 'Amount');
        home_goals_data.addRow(['Goals scored', home_form['GS']]);
        home_goals_data.addRow(['Goals conceded', home_form['GC']]);

        var chart_home_form = new google.visualization.PieChart(document.getElementById('WDL_chart_home'));
        var chart_home_goals = new google.visualization.PieChart(document.getElementById('goals_chart_home'));
        chart_home_form.draw(home_data, options_1);
        chart_home_goals.draw(home_goals_data,options_2);

    // Create away form data table
        var away_data = new google.visualization.DataTable();
        away_data.addColumn('string', 'Result_Outcome');
        away_data.addColumn('number', 'Result_Count');
        away_data.addRow(['Wins', away_form['Won']]);
        away_data.addRow(['Draws', away_form['Drawn']]);
        away_data.addRow(['Losses', away_form['Lost']]);

        var away_goals_data = new google.visualization.DataTable();
        away_goals_data.addColumn('string', 'Amount');
        away_goals_data.addColumn('number', 'Amount');
        away_goals_data.addRow(['Goals scored', away_form['GS']]);
        away_goals_data.addRow(['Goals conceded', away_form['GC']]);

        var chart_away_form = new google.visualization.PieChart(document.getElementById('WDL_chart_away'));
        var chart_away_goals = new google.visualization.PieChart(document.getElementById('goals_chart_away'));
        chart_away_form.draw(away_data, options_1);
        chart_away_goals.draw(away_goals_data,options_2);

  }//end function drawChartPie

});//end document ready function
