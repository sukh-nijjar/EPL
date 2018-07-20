$(document).ready(function() {
    if (typeof(Storage) !== "undefined") {
        console.log("LOCAL STORAGE AVAILBALE");
    } else {
        console.log("LOCAL STORAGE *NOT* AVAILBALE")
    }

    $("#err_resolve").click(function(){
      $("td").each(function() {
        // get the values to populate editable boxes plus pull through name attribute
        // to include on elements dynamically created
        var input_value = $(this).text();
        var name = $(this).attr("name");

        //if value is a number (NOT isNAN!!) and also is not a team name (therefore a goal field)
        if (!isNaN(input_value) && !$(this).hasClass("team_name")){
          $(this).after('<td><input min="0" type="number" value="' + input_value + '" name="' + name + '"/></td>');
          $(this).remove(); //removes the read-only values
        }
        //else it is a team name
        else if ($(this).hasClass("team_name")){
          // $(this).after('<td class="team_name"><input type="text" value="' + input_value + '" name="' + name + '"/></td>');
          $(this).after('<td class="team_name"><input value="' + input_value + '" name="' + name + '"/></td>');
          $(this).remove(); //removes the read-only values
        }
        else if (input_value === 'None'){
          $(this).after('<td><input min="0" type="number" value="0" name="' + name + '"/></td>');
          $(this).remove(); //removes the read-only 'None' values
        }
        // remove the delete option when in edit mode
        $(this).find('.erroneous_result_delete').remove();
        $(this).closest('tr').find('td:nth-child(1)').prop('hidden',true);
        // $('td [name=ID]').prop('hidden',true);
        // $('td [name=ID]').remove();
      });
      // console.log(this); Note - the context of 'this' is dependent on element selected
      $(this).after('<input class="resolve_error_buttons" id="err_cancel" type="button" value="Cancel"/>');
      $(this).after('<input class="resolve_error_buttons" id="err_save" type="button" value="Save"/>');
      $(this).remove();
    });

    $("#invalid_results").on("click", "#err_cancel", function () {
      window.location.href = "/upload_errors/";
    });

    $("#invalid_results").on("click", "#err_save", function () {
      // $('td [type=number]').css('background','blue');
      // $('td [type=number]').each(function (i,value) {
      //   console.log(this)
      //   if (this.value.length === 0) {
      //     this.css('background','red')};
      //   alert("i = " + i + " " + this.value);
      // });
      var deferreds = [];
      $("tr.table_rows").each(function(){
        var ajax = $.ajax({
            data :  {
              home_team : $(this).find('[name=home_team]').val(),
              hftg : $(this).find('td input[name=hftg]').val(),
              hhtg : $(this).find('td input[name=hhtg]').val(),
              ahtg : $(this).find('td input[name=ahtg]').val(),
              aftg : $(this).find('td input[name=aftg]').val(),
              away_team : $(this).find('[name=away_team]').val(),
              resid : $(this).find('[name=ID]').val()
          },
          type : 'PUT',
          url : '/verify_resolved_results/'
        })
        // Push promise to 'deferreds' array
        deferreds.push(ajax);
      }); //end 'each'
      $.when.apply($, deferreds).then(function() {
          window.location.href = "/upload_errors/";
      });
    });

    $(".erroneous_result_delete").on("click",function () {
      var r_id = $(this).closest('tr').find('td[name=ID]').text();
      $.ajax({
        data : {
          resid : r_id
        },
        type : 'DELETE',
        url : '/delete_erroneous_result/'
      })
      .done(function(data) {
        if (data.done) {
          console.log(data);
          $('#master_section').prepend('<h3 id="UI_Msg" class="success_msg">' + data.done +'</h3>');
          toggle_UI_Msg();
        }
      })
    });

    // $("#team_details_name").click(function(){
    //     var team = $(this).text();
    //     $(function() {
    //       $.getJSON("/get_chart_data", {
    //         team : team},
    //           function(data) {
    //             drawChart(data);
    //     });
    //   });
    // });

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
          $('#master_section').prepend('<h3 id="UI_Msg" class="error">Team name is mandatory</h3>');
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
            var r_id = $(this).closest('tr').find('[name=ID]').text(); //gets the hidden record ID from results.html
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
            $(this).closest('tr').find('td:nth-child(1)').before('<td hidden name="ID"><input min="0" name="ID" type="number" value="' + r_id + '"/></td>');//makes ID available in DOM
            $(this).closest('tr').find('td:nth-child(2)').after('<td name="hftg"><input min="0" name="hftg" type="number" value="' + hftg + '"/></td>');
            $(this).closest('tr').find('td:nth-child(3)').after('<td name="hhtg"><input min="0" name="hhtg" type="number" value="' + hhtg + '"/></td>');
            $(this).closest('tr').find('td:nth-child(4)').after('<td name="ahtg"><input min="0" name="ahtg" type="number" value="' + ahtg + '"/></td>');
            $(this).closest('tr').find('td:nth-child(5)').after('<td name="aftg"><input min="0" name="aftg" type="number" value="' + aftg + '"/></td>');
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
              $('#master_section').prepend('<h3 id="UI_Msg" class="success_msg">' + data.done +'</h3>');
              toggle_UI_Msg();
            }
            else {
              // alert(data.error);
              $('#master_section').prepend('<h3 id="UI_Msg" class="error">' + data.error + '</h3>');
              toggle_UI_Msg();
            }
          })
        } //end if action type is *SAVE*
        if (action_type === 'Delete'){
          alert("DELETE CALLED")
          // var r_id = $(this).closest('tr').find('td input[name=ID]').val();
          var r_id = $(this).closest('tr').find('td [name=ID]').val();
          console.log("r-id is " + r_id);
          $.ajax({
            data : {
              resid : r_id
            },
            type : 'DELETE',
            url : '/delete_result/'
          })
          .done(function(data) {
            if (data.done) {
              $('#master_section').prepend('<h3 id="UI_Msg" class="success_msg">' + data.done +'</h3>');
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

      // if ($('#stats_home').length > 0) {
      //   // $('#hmmm').css('visibility','visible');
      //   $('#hmmm').addClass('animated fadeIn');
      //   // console.log('#home element on this page');
      // }

      $('#stats_home').bind('click',function(){
        $('#home').slideToggle();
      });

      $('#stats_away').bind('click',function(){
        $('#away').slideToggle();
      });

      $('#stats_overall').bind('click',function(){
        $('#overall').slideToggle();
      });

      // Load data page:
      // disable button when no file has been selected for uploading:
      $("#upload_results_button").prop('disabled',true);
      // demo messages are hidden until radio button selected:
      $("#valid_file_msg").hide();
      $("#file_with_errors_msg").hide();

      $("#valid_file_RB").bind('click', function(){
        $("#valid_file_msg").show();
        $("#file_with_errors_msg").hide();
        $("#file_load_feedback").hide();
        $("#upload_results_button").prop('disabled',false);
      });

      $("#invalid_file_RB").bind('click', function(){
        $("#file_with_errors_msg").show();
        $("#valid_file_msg").hide();
        $("#file_load_feedback").hide();
        $("#upload_results_button").prop('disabled',false);
      });

      //-- HINTS FUNCTIONALITY --//
      //when page loads close all panels except the first one
      $(".panel_content").not(":first").hide();
      //ensure first panel content is showing on page load
      $(".panel_content:first").show();
      //add a class to denote header is currently the active one
      $(".panel_header:first").addClass("active_header");

      $(".panel_header").click(function(){
          $(".panel_content:visible").slideUp("slow").prev().removeClass("active_header");
          $(this).addClass("active_header").next().slideDown("slow");
      });

      var state = sys_state;
      // set hints panel to either on or off when page loads:
      // if switch 'on' premier league header is hidden
      if (localStorage.getItem("switch_state") == 'on'){
        $("#myonoffswitch").prop("checked",true);
        hint = state_message(state)
        // $("#wrapper").html("<header id='hints'><section class='hint_text'><p>" + hint + "</p></section></header>");
        $("#hints").prop("hidden",false);
        $("#hints").html("<section class='hint_text'><p>" + hint + "</p></section>");
        $("#logo").prop("hidden",true);
        console.log('ON');
      }
      // if switch 'off' hints header is hidden
      else if (localStorage.getItem("switch_state") == 'off'){
        $("#myonoffswitch").prop("checked",false);
        $("#hints").prop("hidden",true);
        $("#logo").prop("hidden",false);
        console.log('OFF');
      }
      else{
        // settings when local storage has not yet been set
        $("#logo").prop("hidden",false);
        $("#hints").prop("hidden",true);
        $("#myonoffswitch").prop("checked",false);
      }

      $("input[name=onoffswitch]").change(function(){
        hint = state_message(state)
        if ($("input[name=onoffswitch]:checked").length){
          localStorage.setItem("switch_state", "on");
          $("#logo").prop("hidden",true);
          // $("#wrapper").html("<header id='hints'><section class='hint_text'><p>" + hint + "</p></section></header>");
          $("#hints").prop("hidden",false);
          $("#hints").addClass("animated fadeInLeftBig");
          $("#hints").html("<section class='hint_text'><p>" + hint + "</p></section>");
        }
        else{
          localStorage.setItem("switch_state", "off");
          $("#logo").prop("hidden",false);
          $("#hints").prop("hidden",true);
          $("#logo").addClass('animated fadeInRightBig');
          $("hints").removeClass('animated fadeInLeftBig');
        }
      });

      // if (localStorage.getItem("switch_state") == 'on'){
      //   $("#myonoffswitch").prop("checked",true);
      // }
      // else{
      //   $("#myonoffswitch").prop("checked",false);
      // }

      //-- END HINTS FUNCTIONALITY --//

});//end top document.ready function

function toggle_UI_Msg(){
  $('#UI_Msg').slideDown();
  window.setTimeout(function(){
       $('#UI_Msg').slideUp(400,function(){
         location.reload(true);
       })},3000);
}

function state_message(state){
  switch (state) {
    case 'NO DATA':
      // $("#new_team").addClass("animated flash");
      return 'At the start of this demo the system contains no teams or results data, so if you view the league table (for example) a message is displayed informing of this fact. The first step is to add some data either through New team or Load data options.';
      break;
    case '1 TEAM':
      return 'One team has been created, however in order to enter results there needs to be a minimum of two teams as a team cannot play itself! Use New team to add a second team.';
      break;
    case 'TEAM AND RESULT EXIST':
      return 'So now both teams and results are populated which means it is possible to visualise various performance metrics - go to Visualization to see this in action.';
      break;
    case 'TEAM DATA EXISTS':
      return 'Now that at least 2 teams have been saved use Enter result to create a result.';
      break;
    case 'ERRORS EXIST':
      return 'The results upload process has identified some errors. Errors can be corrected by selecting the Resolve Errors button or simply deleted.';
      break;
  }
}

// set focus on team name input on create team form
if (typeof $("#teamName").val() === 'undefined'){
  ; //ignore/do nothing as the element is not on the page
}
else{
  $("#teamName").focus();
}
