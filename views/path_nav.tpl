-->
% import shared_cfg
<a class="a link-text path-component-link" href="/manage">(Root)</a>
% folders = path.split("/")
% encoded_path = "+"
% for f in folders:
    % if len(f):
        % if len(encoded_path) > 1:
            % encoded_path += "+"
        % end
        % encoded_path += f
        <a class="a link-text path-component-link" href="/manage{{encoded_path}}">/ {{f}}</a>
    % end
% end
<!--