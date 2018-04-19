$(document).ready(function() {

  // Load the Visualization API and the corechart package.
  google.charts.load('current', {'packages':['corechart']});
  google.charts.load('current', {'packages':['bar']});
  google.charts.load('current', {'packages':['line']});

  var chart = chart_to_load;
  team_data = JSON.parse(teams); //note this kills the order of the dict!!

  //decide which chart to invoke
  switch(chart){
    case 'barChartGames':
      google.charts.setOnLoadCallback(drawChartWDL);
      break;
    case 'barChartPoints':
      google.charts.setOnLoadCallback(drawChartPts);
      break;
    case 'lineChart':
      google.charts.setOnLoadCallback(drawChartTrend);
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
        title: 'By Wins, draws and defeats',
        bar: { groupWidth: '61.8%' },
        isStacked: false,
        orientation: 'vertical',
        colors:['red', 'orange', 'green'],
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
      title: 'By points',
      bar: { groupWidth: '61.8%' },
      isStacked: true,
      orientation: 'horizontal',
      colors:['green','blue'],
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
  }
});//end document ready function
