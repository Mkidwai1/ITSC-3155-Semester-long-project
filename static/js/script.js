// Function to handle opening the navigation sidebar
function openNav() {
    document.getElementById("navbar").style.width = "250px";
}

// Function to handle closing the navigation sidebar
function closeNav() {
    document.getElementById("navbar").style.width = "0";
}

// Calendar JS logic below

//debugging check to see if calendar loads properly
console.log('FullCalendar is:', typeof FullCalendar !== 'undefined' ? 'Loaded' : 'Not loaded');

document.addEventListener('DOMContentLoaded', function () {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        schedulerLicenseKey: 'CC-Attribution-NonCommercial-NoDerivatives',
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: calendarEvents.map(event => ({
            title: event.title,
            start: event.start_at,
        })),
        dateClick: function (info) {
            // Populate the modal for new event
            $('#dueDate').val(info.dateStr);
            $('#eventModal').modal('show');
        },
        eventClick: function (info) {
            var eventObj = info.event;
            $('#editAssignmentName').val(eventObj.title);
            $('#editDueDate').val(eventObj.start.toISOString().substring(0, 10));
            // Populate other fields if necessary
            $('#editEventModal').modal('show');
        }
    });

    calendar.render();

    // Separate click handler for updating the event
    $('#updateEvent').on('click', function () {
        // Ensure eventObj is available here
        var eventObj = calendar.getEventById($('#eventId').val());
        if (!eventObj) {
            console.error('Event not found');
            return;
        }

        var updatedEventData = {
            event_id: eventObj.id,
            title: $('#editAssignmentName').val(),
            start_date: $('#editDueDate').val() + 'T' + ($('#editEventTime').val() || '00:00'), // Adjust as necessary

        };




        $('#editEventModal').modal('hide');
    });



    calendar.render();

    // Handle saving new event from the modal
    $('#saveEvent').on('click', function () {
        var eventType = $('#eventType').val();
        var assignmentName = $('#assignmentName').val();
        var dueDate = $('#dueDate').val();
        var eventTime = $('#eventTime').val();
        var eventLocation = $('#eventLocation').val();
        var eventClass = $('#eventClass').val();

        var eventData = {
            title: assignmentName + ' - ' + eventType,
            start: dueDate + 'T' + (eventTime || '00:00'), // If time is not provided, default to '00:00'
            location: eventLocation,
            className: eventClass

        };

        // Ensure all necessary fields are filled
        if (eventData.title && eventData.start) {
            calendar.addEvent(eventData);
            $('#eventModal').modal('hide'); // Close the modal after adding the event
        } else {
            alert('Please fill in all required fields.');
        }

    });


    // Handle event type change in the modal
    $('#eventType').on('change', function () {
        var selectedType = $(this).val();
        $('#dateGroup, #timeGroup, #locationGroup, #classGroup').hide();
        if (selectedType === 'homework' || selectedType === 'project') {
            $('#dateGroup, #classGroup').show();
        } else if (selectedType === 'class' || selectedType === 'meeting') {
            $('#timeGroup, #locationGroup').show();
        }
    }).trigger('change');

});


// Function to convert Canvas API events to FullCalendar events
function convertCanvasEventsToFullCalendarEvents(canvasEvents) {
    return canvasEvents.map(event => {
        return {
            title: event['title'],
            start: event['start_at']
        };
    }).filter(event => event.start); // Filter out events without a start date
}


$(document).ready(function() {
    // Handling the click on shop items to initiate purchase
    $('.shop-item').click(function() {
        var itemId = $(this).data('item-id');
        var name = $(this).data('name');
        var price = $(this).data('price');
        var img = $(this).data('img');
        var isPurchased = $(this).hasClass('purchased');

        if (!isPurchased) {
            $('#purchaseItemImg').attr('src', img);
            $('#purchaseModalLabel').text('Confirm Purchase: ' + name);
            $('#purchaseItemPrice').text('Price: ' + price + ' coins');
            $('#confirmPurchase').data('item-id', itemId).data('price', price);
            $('#purchaseModal').modal('show');
        }
    });

    // Confirm purchase and update inventory
    $('#confirmPurchase').on('click', function() {
        var itemId = $(this).data('item-id');
        var price = $(this).data('price');

        $.ajax({
            url: '/buy-item',
            type: 'POST',
            data: { item_id: itemId },
            success: function(response) {
                if (response.success) {
                    $('#purchaseModal').modal('hide');
                    alert('Purchase successful!');
                    // Optionally reload or dynamically update the page content
                    addAvatarToInventory(itemId, response.avatarUrl);
                } else {
                    alert('Purchase failed: ' + response.message);
                }
            },
            error: function(xhr) {
                alert('Error: ' + xhr.statusText);
            }
        });
    });
});

function updateInventory(itemId, imgUrl) {
    var newAvatarMarkup = `<div class="inventory-item" data-item-id="${itemId}" data-img="${imgUrl}" onclick="selectAvatar(this)">
                               <img src="${imgUrl}" alt="Avatar">
                               <p>Selected</p>
                           </div>`;
    $('#inventory').append(newAvatarMarkup);
}

$(document).ready(function() {
    $('.inventory-item').click(function() {
        const itemId = $(this).data('item-id');
        $.ajax({
            url: '/set-avatar',
            type: 'POST',
            data: { item_id: itemId },
            success: function(response) {
                if (response.success) {
                    $('.inventory-item').removeClass('selected');  // Remove the class from all items
                    $(this).addClass('selected');  // Add the class to the selected item
                    window.location.reload();
                    alert(response.message);
                } else {
                    alert(response.message);
                }
            },
            error: function() {
                alert('Error updating avatar. Please try again.');
            }
        });
    });
});


function unlockAllThemes() {
    $.ajax({
        url: "/unlock-color-picker", // Ensure this URL is correct
        type: "POST",
        success: function(response) {
            if (response.success) {
                alert('Themes unlocked successfully!');
                $('.color-picker fieldset').removeAttr('disabled'); // Enable the color picker
                window.location.reload(); // Optional: Reload the page to reflect changes
            } else {
                alert('Failed to unlock themes: ' + response.message);
            }
        },
        error: function(xhr) {
            alert('Failed to unlock themes. Error: ' + xhr.responseText);
        }
    });
}

// Apply theme from local storage on load
window.onload = function() {
    var theme = localStorage.getItem('theme');
    if (theme) {
        document.getElementById(theme).checked = true;
        applyTheme(theme);
    }
};

// Function to apply the selected theme
function applyTheme(theme) {
    document.documentElement.className = theme;
}

// Event listeners for theme radio buttons
document.querySelectorAll('input[name="theme"]').forEach(input => {
    input.addEventListener('change', function() {
        if (!this.parentNode.hasAttribute('disabled')) {
            localStorage.setItem('theme', this.id);
            applyTheme(this.id);
        }
    });
});
