from .content import load_portfolio_context


def portfolio_context(request):
    return load_portfolio_context()
