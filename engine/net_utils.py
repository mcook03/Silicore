def contains_any_keyword(text, keywords):
    upper_text = text.upper()
    return any(keyword.upper() in upper_text for keyword in keywords)


def is_power_net(net_name, power_keywords):
    return contains_any_keyword(net_name, power_keywords)


def is_ground_net(net_name, ground_keywords):
    return net_name.upper() in {keyword.upper() for keyword in ground_keywords}


def is_excluded_net(net_name, excluded_keywords):
    return contains_any_keyword(net_name, excluded_keywords)


def is_critical_signal_net(net_name, critical_keywords):
    return contains_any_keyword(net_name, critical_keywords)