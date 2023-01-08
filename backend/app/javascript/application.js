// Entry point for the build script in your package.json
import "@hotwired/turbo-rails";

import embed from "vega-embed";

window.vegaEmbed = embed;
window.dispatchEvent(new Event("vega:load"));

import "./controllers";
