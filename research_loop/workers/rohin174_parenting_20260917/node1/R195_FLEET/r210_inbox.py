"""Only introduce R210 parent and attributed peer relays at THINK boundaries."""


def think_incoming(incoming, stage):
    if stage == 'THINK':
        return incoming
    return [event for event in incoming if not event.text.startswith(('Astra: [R210_PARENT]', 'Astra: [R210_PEER]'))]
