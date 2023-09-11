class Frame extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
    }

    connectedCallback() {
        const config = JSON.parse(this.getAttribute('config'));
        this.render(config);
    }

    render(config) {
        this.shadowRoot.innerHTML = `
            <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">

            <style>
                #sidebar {
                    background-color: ${config.config.sidebarColor};
                    height: 100vh;
                }
                #topbar {
                    background-color: ${config.config.headerColor};
                }
            </style>

            <div class="container-fluid">
                <div class="row">
                    <nav id="sidebar" class="col-md-3 col-lg-2 d-md-block bg-light sidebar">
                        Welcome ${config.profile.name}
                        ${config.menu.map(item => `
                            <div class="position-sticky">
                                <ul class="nav flex-column">
                                    <li class="nav-item">
                                        <a class="nav-link" href="${item.url}">
                                            ${item.icon ? `<img src="${item.icon}" alt="${item.name} icon">` : ''}
                                            ${item.name}
                                        </a>
                                    </li>
                                </ul>
                            </div>
                        `).join('')}
                    </nav>

                    <main role="main" class="col-md-9 ml-sm-auto col-lg-10 px-md-4">
                        <div id="topbar" class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">                            
                            <div class="btn-toolbar mb-2 mb-md-0">
                                <!-- Add more top bar elements here -->
                            </div>
                        </div>
                        <slot></slot>
                    </main>
                </div>
            </div>
        `;
    }
}

customElements.define('data-frame', Frame);
