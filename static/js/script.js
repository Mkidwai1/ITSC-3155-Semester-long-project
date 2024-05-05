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


document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    var currentEventId, currentEventUrl;  // To store the event ID and URL globally
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: calendarEvents,  // Use the events from the backend
        dateClick: function(info) {
            $('#dueDate').val(info.dateStr);
            $('#newEventModal').modal('show');
        },
        eventClick: function(info) {
            info.jsEvent.preventDefault(); 
            var eventObj = info.event;
            console.log(eventObj);
            currentEventId = eventObj.id;
            currentEventUrl = eventObj.url;
            // Populate editing modal fields
            $('#editingEventModal').find('#eventName').val(eventObj.title);
            $('#editingEventModal').find('#dueDate').val(eventObj.start.toISOString().substring(0, 10));
            $('#editingEventModal').find('#eventTime').val(eventObj.start.toTimeString().substring(0, 5));
            $('#editingEventModal').modal('show');
        }
    });
    calendar.render();

    $('#newEventForm').on('submit', function(e) {
        e.preventDefault(); // Prevent default form submission

    
        var eventData = {
            title: $('#eventName').val(),
            start: $('#dueDate').val(),
            url: $('#eventURL').val(),  // Assuming there's a field for URL
            type: $('#eventType').val() // Example type
        };
    
        $.ajax({
            url: '/frontend-add-event',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(eventData),
            success: function(response) {
                console.log('response');
                if (response.success) {
                    console.log('response success')
                    $('#newEventModal').modal('hide');
                    calendar.addEvent({
                        title: eventData.title,
                        start: eventData.start,
                        url: eventData.url
                    });
                    console.log('event added to calendar');
                    alert('Event added successfully.');
                    window.location.reload();
                } else {
                    alert('Failed to add event: ' + response.message);
                }
            },
            error: function(xhr, status, error) {
                alert('Error adding event: ' + error);
            }
        });
    });
    
    // Button click to redirect to the event URL
    $('#goToEvent').on('click', function() {
        if(currentEventUrl) {
            window.open(currentEventUrl, '_blank');
        }
    });

    // Button click to delete an event
    $('#deleteEvent').on('click', function() {
        console.log('Delete button clicked');
        if (confirm('Are you sure you want to delete this event?')) {
            console.log('Confirmed deletion for event ID:', currentEventId);
            $.ajax({
                url: '/delete-event',
                type: 'POST',
                data: { id: currentEventId },  // Ensure this ID is what you expect
                success: function(response) {
                    console.log('Response from server:', response);
                    if (response.success) {
                        var event = calendar.getEventById(currentEventId);  // Retrieve the event object
                        console.log('Found event in calendar:', event);
                        if (event) {
                            event.remove();  // Remove the event from FullCalendar
                            console.log('Event removed from FullCalendar');
                        }
                        $('#editingEventModal').modal('hide');
                        alert('Event deleted successfully.');
                    } else {
                        alert('Failed to delete the event. Server message: ' + response.message);
                    }
                },
                error: function(xhr, status, error) {
                    console.error('AJAX error:', error);
                    alert('Error occurred while deleting the event: ' + error);
                }
            });
        } else {
            console.log('Deletion cancelled by user');
        }
    });
    
    

    $('#saveEvent').on('click', function() {
        
    
        // If an event ID is present, update the existing event.
        if (currentEventId) {
            $('#eventModal').modal('hide');
            
        } else {
            var eventData = {
                title: $('#eventName').val() + ' - ' + $('#eventType').val(),
                start: $('#dueDate').val() + 'T' + $('#eventTime').val(),
                location: $('#eventLocation').val(),
                className: $('#eventClass').val()
            };
            // If no current event ID, add a new event to the calendar.
            calendar.addEvent(eventData);
            // Close the modal after adding a new event
            $('#eventModal').modal('hide');
        }
    });
    

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


function deleteMessage(messageId) {
    console.log("Emitting delete for message ID:", messageId);  // Debug log
    if (messageId) {
        socket.emit('delete_message', { message_id: messageId });
    } else {
        console.error("Attempted to delete a message without a valid ID");
    }
}

document.getElementById('delete-last-msg').addEventListener('click', function() {
    socket.emit('delete_last_message');
    console.log('Request to delete last message sent');
    window.location.reload();
});

