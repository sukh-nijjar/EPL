$(document).ready(function() {
    console.log('Calling my_JQ.js')
    google.charts.load('current', {'packages':['corechart']});

    // if ($('#teamDetails').length) {
    //   alert("on team details page")
    //   alert(data);
    //   // alert($('#team_details_name').text());
    //   google.charts.load('current', {'packages':['corechart']});
    //   // google.charts.setOnLoadCallback(drawChart);
    // }

    $("#err_resolve").click(function(){
      console.log("resolve button clicked")
      $("td").each(function() {
        // get the values to populate editable boxes plus pull through name attribute
        // to include on elements dynamically created
        var input_value = $(this).text();
        var name = $(this).attr("name");

        //if value is a number (NOT isNAN!!) and also is not a team name
        if (!isNaN(input_value) && !$(this).hasClass("team_name")){
          $(this).after('<td><input min="0" type="number" value="' + input_value + '" name="' + name + '"/></td>');
          $(this).remove(); //removes the read-only values
        }
        //else it is a team name
        else if ($(this).hasClass("team_name")){
          $(this).after('<td class="team_name"><input type="text" value="' + input_value + '" name="' + name + '"/></td>');
          $(this).remove(); //removes the read-only values
        }
      });
      // console.log(this); Note - the context of 'this' is dependent on element selected
      $(this).after('<input class="resolve_error_buttons" id="err_cancel" type="button" value="Cancel"/>');
      $(this).after('<input class="resolve_error_buttons" id="err_save" type="button" value="Save"/>');
      $(this).remove();
    });

    $("#invalid_results").on("click", "#err_cancel", function () {
      location.reload(true);
    });

    $("#invalid_results").on("click", "#err_save", function () {
      $("tr.table_rows").each(function(){
        console.log($(this));
        $.ajax({
          data :  {
            home_team : $(this).find('[name=home_team]').val(),
            hftg : $(this).find('td input[name=hftg]').val(),
            hhtg : $(this).find('td input[name=hhtg]').val(),
            ahtg : $(this).find('td input[name=ahtg]').val(),
            aftg : $(this).find('td input[name=aftg]').val(),
            away_team : $(this).find('[name=away_team]').val()
          },
          type : 'PUT',
          url : '/update_score/'
        })
        // .done(
      })
    });

    $("#team_details_name").click(function(){
        var team = $(this).text();
        $(function() {
          $.getJSON("/get_chart_data", {
            team : team},
              function(data) {
                drawChart(data);
        });
      });
    });

    $('#submitSaveTeam').on('click', function(e) {
        e.preventDefault();
        if ( $('.error').length ){
          $('.error').remove();
        }
        var teamName = $('#teamName').val();
        if (teamName.trim().length > 0){
          $('#create_team').submit();
        }
        else {
          $('section').prepend('<h3 id="UI_Msg" class="error">Team name is mandatory</h3>');
          toggle_UI_Msg();
        }
     });

    $('#submitDeleteAllTeams').on('click', function(e) {
           e.preventDefault();
           $("#dialog-confirm").dialog({
             title: "Delete all teams?",
             resizable: false,
             //autoOpen: false,
             height: "auto",
             width: 400,
             modal: true,
             buttons: {
               "No, do not delete all teams": function() {
                 $( this ).dialog( "close" );
               },
               "Yes, delete all teams": function() {
                 $("#deleteAllTeams").submit();
               }
             } //end buttons
           });
    });

    $('tr').delegate('td.action_link', 'click', function(e) {
      $this = $(this);
      var action_type = $this.find('a').text();
      if (action_type === 'Edit'){
          if ($(this).closest('tr').hasClass('fixture')){
            // alert("Fixture class row");
            $(this).closest('tr').css('background-color','#44c154').find('input').prop('disabled', false);
            $(this).after('<td class="action_link"><a class="AL_cancel" href="#">Cancel</a></td>');
            $(this).after('<td class="action_link"><a class="AL_save" href="#">Save</a></td>');
            $(this).remove();
          } else /*result*/ {
            var hftg = $(this).closest('tr').find('[name=hftg]').text();
            var hhtg = $(this).closest('tr').find('[name=hhtg]').text();
            var ahtg = $(this).closest('tr').find('[name=ahtg]').text();
            var aftg = $(this).closest('tr').find('[name=aftg]').text();
            // alert("It's a result class row");
            $(this).closest('tr').css('background-color','#44c154');
            $(this).closest('tr').each(function(){
              $(this).find('td').not('.action_link, .team').remove();
            });
            $(this).after('<td class="action_link"><a class="AL_cancel" href="#">Cancel</a></td>');
            $(this).after('<td class="action_link"><a class="AL_delete" href="#">Delete</a></td>');
            $(this).after('<td class="action_link"><a class="AL_save" href="#">Save</a></td>');
            $(this).closest('tr').find('td:nth-child(1)').after('<td name="hftg"><input min="0" name="hftg" type="number" value="' + hftg + '"/></td>');
            $(this).closest('tr').find('td:nth-child(2)').after('<td name="hhtg"><input min="0" name="hhtg" type="number" value="' + hhtg + '"/></td>');
            $(this).closest('tr').find('td:nth-child(3)').after('<td name="ahtg"><input min="0" name="ahtg" type="number" value="' + ahtg + '"/></td>');
            $(this).closest('tr').find('td:nth-child(4)').after('<td name="aftg"><input min="0" name="aftg" type="number" value="' + aftg + '"/></td>');
            $(this).remove();
          }
        } //end if action type is *EDIT*
        if (action_type === 'Cancel'){
          location.reload(true);
        } //end if action type is *CANCEL*
        if (action_type === 'Save'){
          $.ajax({
            data :  {
              home_team : $(this).closest('tr').find('[name=home_team]').text(),
              hftg : $(this).closest('tr').find('td input[name=hftg]').val(),
              hhtg : $(this).closest('tr').find('td input[name=hhtg]').val(),
              ahtg : $(this).closest('tr').find('td input[name=ahtg]').val(),
              aftg : $(this).closest('tr').find('td input[name=aftg]').val(),
              away_team : $(this).closest('tr').find('[name=away_team]').text()
            },
            type : 'PUT',
            url : '/update_score/'
          })
          .done(function(data) {
            if (data.done) {
              $('section').prepend('<h3 id="UI_Msg" class="success_msg">' + data.done +'</h3>');
              toggle_UI_Msg();
            }
            else {
              // alert(data.error);
              $('section').prepend('<h3 id="UI_Msg" class="error">' + data.error + '</h3>');
              toggle_UI_Msg();
            }
          })
        } //end if action type is *SAVE*
        if (action_type === 'Delete'){
          alert("DELETE CALLED")
          $.ajax({
            data : {
              home_team : $(this).closest('tr').find('[name=home_team]').text(),
              away_team : $(this).closest('tr').find('[name=away_team]').text()
            },
            type : 'DELETE',
            url : '/delete_result/'
          })
          .done(function(data) {
            if (data.done) {
              $('section').prepend('<h3 id="UI_Msg" class="success_msg">' + data.done +'</h3>');
              toggle_UI_Msg();
            }
          })
        } //end if action type is *DELETE*
    }); //function end

    var team = $('#team_details_name').text();
    $("tr.result_row").each(function() {
      $this = $(this);
      var row_team = $this.find("td.home_team").text();
      var home = $this.find("td.home").text();
      var away = $this.find("td.away").text();
      if (row_team === team){
        if (home > away) {
          $(this).find('td.result_type').append('<img src="/static/images/win.png"/>');
        } else if (away > home) {
          $(this).find('td.result_type').append('<img src="/static/images/loss.png"/>');
        } else {
          $(this).find('td.result_type').append('<img src="/static/images/draw.png"/>');
        }
      }
      if (row_team != team) {
        if (home > away) {
          $(this).find('td.result_type').append('<img src="/static/images/loss.png"/>');
        } else if (away > home) {
          $(this).find('td.result_type').append('<img src="/static/images/win.png"/>');
        } else {
          $(this).find('td.result_type').append('<img src="/static/images/draw.png"/>');
        }
      }
    });

       $( ".selectmenu" ).selectmenu();
       $(".spinner").spinner({
          min: 0
       });

       $( "#menu" ).menu();
       $(" #GDToolTip ").tooltip();


      $('.error').fadeIn("slow");
      $('.feedback').fadeIn("slow");
      $('.success_msg').fadeIn("slow");
      $('.warning').fadeIn("slow");

      // // set focus on team name input on create team form
      // $('#teamName').bind('focus,' function(){
      //   $(this).css('border', '1px solid blue');
      // });


});//end top document.ready function

function toggle_UI_Msg(){
  // $('section').prepend('<h3 id="UI_Msg" class="success_msg">' + data.done +'</h3>');
  $('#UI_Msg').slideDown();
  window.setTimeout(function(){
       $('#UI_Msg').slideUp(400,function(){
         location.reload(true);
       })},3000);
}

function drawChart(t) {
  // Create the data table.
  $('#chart_div').slideToggle(1000);
  var data = new google.visualization.DataTable();
  data.addColumn('string', 'Result_Outcome');
  data.addColumn('number', 'Result_Count');
  data.addRows([
    ['Wins', t.won],
    ['Draws', t.drawn],
    ['Losses', t.lost]
  ]);
  //
  // // Set chart options
  var options = {'title':'Performance',
                 'width':600,
                 'height':400,
                 'pieHole': 0.3,
                 'colors': ['green', 'orange', 'red']};
  //
  // // Instantiate and draw our chart, passing in some options.
  var chart = new google.visualization.PieChart(document.getElementById('chart_div'));
  chart.draw(data, options);
}

// set focus on team name input on create team form
// document.getElementById("teamName").focus();
