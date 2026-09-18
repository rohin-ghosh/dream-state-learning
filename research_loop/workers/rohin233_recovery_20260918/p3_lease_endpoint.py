"""Exact P3 publication transport with the newly reported node4 horizon."""

import inspect

import p3_endpoint


END_UNIX = 1790359200


def main():
    source = inspect.getsource(p3_endpoint.main)
    previous = 'time.time() < predecessor.WALL'
    if source.count(previous) != 1:
        raise ValueError('exact_endpoint_deadline_projection')
    namespace = dict(vars(p3_endpoint), END_UNIX=END_UNIX)
    exec(compile(source.replace(previous, 'time.time() < END_UNIX'),
        __file__ + ':endpoint', 'exec'), namespace)
    namespace['main']()


if __name__ == '__main__':
    main()
