
const routes = {
    user: {
        title: 'Welcome Home',
        render: container => {
            container.innerHTML = `
        <p>This is the home page.</p>
        <button id="alert-btn">Click me!</button>
      `;
            document.getElementById('alert-btn')
                .addEventListener('click', () => alert('Hello from Home!'));
        }
    },
    between: {
        title: 'About Us',
        render: container => {
            container.innerHTML = `
        <p>We’re a small startup building cool things.</p>
        <ul>
          <li>Vanilla JS</li>
          <li>No frameworks</li>
        </ul>
      `;
        }
    },
    home: {
        title: 'Full Graph',
        render: container => {
            container.innerHTML = `
        <form id="contact-form">
          <label>
            Your Name:
            <input type="text" name="name" required>
          </label><br><br>
          <label>
            Message:
            <textarea name="message" required></textarea>
          </label><br><br>
          <button type="submit">Send</button>
        </form>
      `;
            document.getElementById('contact-form')
                .addEventListener('submit', e => {
                    e.preventDefault();
                    const data = new FormData(e.target);
                    console.log('Contact form submitted:', {
                        name: data.get('name'),
                        message: data.get('message')
                    });
                    alert('Thanks for reaching out!');
                });
        }
    }
};


function router() {
    console.log("Hashing Route")
    const hash = location.hash.slice(1) || 'home';  // default to “home”
    const route = routes[hash] || routes.home;
    
    // Update the <h1>
    document.getElementById('page-title').textContent = route.title;

    // Render the content
    const contentDiv = document.getElementById('content');
    contentDiv.innerHTML = '';      // clear out old content
    route.render(contentDiv);
}

// Listen for hash changes and initial load
window.addEventListener('hashchange', router);
window.addEventListener('DOMContentLoaded', router);
